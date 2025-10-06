from datetime import datetime
from typing import Dict, List, Any, Optional
from statistics import median, mean

from core.logger import Logger
from core.enums import Status
from services.jira.models.issue import Issue
from .issue_service import IssueService


class CycleTimeAnalyzer:
    """Dedicated analyzer for cycle time metrics."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()
        self.issue_service = IssueService(jira_client)

    def analyze_cycle_time_metrics(
        self,
        project: str,
        scrum_board_ids: List[int],
        sprint_filter_config: Dict[str, Any] = None,
        collection_frequency: str = "sprint_wise",
        kanban_issues: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze cycle time metrics for the specified configuration.

        Args:
            project: Project key
            scrum_board_ids: List of scrum board IDs (includes both Scrum and Kanban boards)
            sprint_filter_config: Sprint filtering configuration
            collection_frequency: 'sprint_wise' or 'monthly' or 'quarterly'
            kanban_issues: Pre-fetched Kanban issues to integrate into sprints

        Returns:
            Dictionary containing cycle time metrics
        """
        self.logger.info(f"Starting cycle time analysis for project: {project}")

        results = {
            "project": project,
            "collection_frequency": collection_frequency,
            "metric_collection": {
                "total_issues_analyzed": 0,
                "date_range": None,
                "aggregate_display": self._get_aggregate_display_format(
                    collection_frequency
                )
            },
            "tool": "Jira with automated cycle time plugin",
            "average_cycle_time": {
                "value": 0,
                "unit": "days",
                "description": "Average time from 'In Progress' to 'Done'"
            },
            "longest_cycle_time": {
                "value": 0,
                "unit": "days",
                "single_longest_issue": None,
                "description": ("The single longest issue took X days due to "
                                "external dependency")
            },
            "analysis": {
                "bottlenecks": [],
                "time_distribution": {},
                "description": ("Where tasks are spending the most time? "
                                "Any big changes from last time?")
            },
            "improvement_steps": {
                "immediate": [],
                "long_term": [],
                "description": ("We'll define acceptance criteria earlier; "
                                "Long-term: e.g., 'We'll add a dedicated QA "
                                "person to reduce wait'")
            },
            "additional_comments": {
                "noteworthy_exceptions": [],
                "context": [],
                "description": ("Link to screenshots of cycle time reports "
                                "or highlight noteworthy exceptions")
            },
            "boards": [],
            "sprints_reference": [],  # Store sprints for Kanban issue mapping
            "filter_config_used": sprint_filter_config
        }

        try:
            from .board_service import BoardService
            from .sprint_service import SprintService

            board_service = BoardService(self.jira)
            sprint_service = SprintService(self.jira)

            # Get boards for the project
            boards = board_service.get_boards_for_project(project)
            all_boards = board_service.filter_scrum_boards(
                boards, scrum_board_ids
            )

            # Separate Scrum and Kanban boards
            scrum_boards = []
            kanban_boards = []

            for board in all_boards:
                sprints = sprint_service.get_sprints_for_board(
                    board.id, sprint_filter_config
                )
                if sprints and len(sprints) > 0:
                    scrum_boards.append((board, project))
                else:
                    kanban_boards.append((board, project))

            self.logger.info(
                f"Project {project}: Found {len(scrum_boards)} Scrum boards and {len(kanban_boards)} Kanban boards"
            )

            # Use pre-fetched Kanban issues if provided, otherwise fetch them
            if kanban_issues is not None:
                self.logger.info(f"Using {len(kanban_issues)} pre-fetched Kanban issues")
                all_kanban_issues = kanban_issues
            else:
                # Fetch Kanban issues from Kanban boards in this project
                all_kanban_issues = []
                for kanban_board, kanban_project in kanban_boards:
                    date_filter = sprint_filter_config.get("date_range") if sprint_filter_config else None
                    board_kanban_issues = self.issue_service.get_all_issues_for_board(
                        kanban_project, kanban_board.id, date_filter
                    )
                    self.logger.info(
                        f"Fetched {len(board_kanban_issues)} issues from Kanban board: {kanban_board.name} "
                        f"(ID: {kanban_board.id}, Project: {kanban_project})"
                    )
                    all_kanban_issues.extend(board_kanban_issues)

            # Second pass: Analyze Scrum boards with sprint-based analysis
            # Integrate Kanban issues into each sprint based on date overlap
            all_issues = []
            for board, board_project in scrum_boards:
                board_result = self._analyze_scrum_board_with_kanban_integration(
                    board, board_project, sprint_filter_config,
                    board_service, sprint_service, all_kanban_issues
                )
                results["boards"].append(board_result)
                all_issues.extend(board_result.get("all_issues", []))

            # Calculate overall cycle time metrics
            if all_issues:
                overall_metrics = self._calculate_overall_cycle_time_metrics(all_issues, collection_frequency)
                results.update(overall_metrics)

                # Add overall best/worst across all sprints by issue type
                results["overall_best_worst"] = self._get_overall_best_worst_by_type(all_issues)

        except Exception as e:
            self.logger.error(f"Error analyzing cycle time for project {project}: {e}")
            raise

        return results

    def _analyze_scrum_board_with_kanban_integration(
        self,
        board: Any,
        project: str,
        sprint_filter_config: Dict[str, Any],
        board_service,
        sprint_service,
        kanban_issues: List[Any]
    ) -> Dict[str, Any]:
        """Analyze Scrum board and integrate Kanban issues into each sprint."""
        self.logger.debug(
            f"Analyzing Scrum board with Kanban integration: {board.name} (ID: {board.id})"
        )

        board_result = {
            "board_info": board_service.get_board_info(board),
            "sprints": [],
            "all_issues": []
        }

        try:
            sprints = sprint_service.get_sprints_for_board(
                board.id, sprint_filter_config
            )

            for sprint in sprints:
                # Get Scrum sprint issues
                sprint_result = self._analyze_sprint_cycle_time(sprint, project)

                # Filter Kanban issues that overlap with this sprint's date range
                kanban_issues_in_sprint = self._filter_kanban_issues_for_sprint(
                    kanban_issues, sprint
                )

                if kanban_issues_in_sprint:
                    self.logger.info(
                        f"Integrating {len(kanban_issues_in_sprint)} Kanban issues into sprint {sprint.name}"
                    )

                    # Calculate cycle time for Kanban issues in this sprint context
                    for issue in kanban_issues_in_sprint:
                        cycle_time_data = self._calculate_issue_cycle_time_for_sprint(issue, sprint)
                        if cycle_time_data:
                            sprint_result["issues_with_cycle_time"].append({
                                "issue": self.issue_service.get_issue_info(issue),
                                **cycle_time_data
                            })

                    # Recalculate sprint summary with integrated issues
                    sprint_result["cycle_time_summary"] = self._summarize_sprint_cycle_time(
                        sprint_result["issues_with_cycle_time"]
                    )

                board_result["sprints"].append(sprint_result)
                board_result["all_issues"].extend(
                    sprint_result.get("issues_with_cycle_time", [])
                )

        except Exception as e:
            self.logger.error(f"Error analyzing Scrum board {board.id}: {e}")

        return board_result

    def _filter_kanban_issues_for_sprint(
        self, kanban_issues: List[Any], sprint: Any
    ) -> List[Any]:
        """Filter Kanban issues that fall within a sprint's date range."""
        from dateutil.parser import isoparse

        try:
            sprint_start = isoparse(sprint.start_date)
            sprint_end = isoparse(sprint.end_date) if sprint.end_date else None

            filtered_issues = []
            for issue in kanban_issues:
                # Parse issue creation date
                created_time = isoparse(issue.fields.created.replace("Z", "+00:00"))

                # Check if issue was created within sprint date range
                # OR if issue was completed within sprint date range
                if created_time >= sprint_start:
                    if sprint_end is None or created_time <= sprint_end:
                        filtered_issues.append(issue)
                        continue

                # Also check if issue was updated/completed during sprint
                updated_time = isoparse(issue.fields.updated.replace("Z", "+00:00"))
                if updated_time >= sprint_start:
                    if sprint_end is None or updated_time <= sprint_end:
                        filtered_issues.append(issue)
                        continue

            return filtered_issues

        except Exception as e:
            self.logger.error(f"Error filtering Kanban issues for sprint {sprint.name}: {e}")
            return []

    def _analyze_board_cycle_time(
        self,
        board: Any,
        project: str,
        sprint_filter_config: Dict[str, Any],
        board_service,
        sprint_service
    ) -> Dict[str, Any]:
        """Analyze cycle time for a single board."""
        self.logger.debug(
            f"Analyzing cycle time for board: {board.name} (ID: {board.id})"
        )

        board_result = {
            "board_info": board_service.get_board_info(board),
            "sprints": [],
            "all_issues": [],
            "is_kanban": False
        }

        try:
            sprints = sprint_service.get_sprints_for_board(
                board.id, sprint_filter_config
            )

            # Check if this is a Kanban board (no sprints)
            if not sprints or len(sprints) == 0:
                self.logger.info(f"Board {board.name} has no sprints, treating as Kanban board")
                board_result["is_kanban"] = True

                # Get all issues for the board using date filter
                date_filter = sprint_filter_config.get("date_range") if sprint_filter_config else None
                all_kanban_issues = self.issue_service.get_all_issues_for_board(
                    project, board.id, date_filter
                )

                # If we have Scrum sprints from other boards, analyze Kanban issues per sprint period
                # Otherwise, analyze all Kanban issues together
                kanban_result = self._analyze_kanban_cycle_time(
                    all_kanban_issues, board.name, project
                )
                board_result["sprints"].append(kanban_result)
                board_result["all_issues"].extend(
                    kanban_result.get("issues_with_cycle_time", [])
                )
            else:
                # Regular sprint-based analysis
                for sprint in sprints:
                    sprint_result = self._analyze_sprint_cycle_time(sprint, project)
                    board_result["sprints"].append(sprint_result)
                    board_result["all_issues"].extend(
                        sprint_result.get("issues_with_cycle_time", [])
                    )

        except Exception as e:
            self.logger.error(f"Error analyzing cycle time for board {board.id}: {e}")

        return board_result

    def _analyze_kanban_cycle_time(self, issues: List[Any], board_name: str, project: str) -> Dict[str, Any]:
        """Analyze cycle time for Kanban board issues (no sprint context)."""
        self.logger.debug(
            f"Analyzing cycle time for Kanban board: {board_name} with {len(issues)} issues"
        )

        # Calculate cycle time for each issue without sprint context
        issues_with_cycle_time = []
        for issue in issues:
            cycle_time_data = self._calculate_issue_cycle_time_no_sprint(issue)
            if cycle_time_data:
                issues_with_cycle_time.append({
                    "issue": self.issue_service.get_issue_info(issue),
                    **cycle_time_data
                })

        return {
            "sprint_info": {
                "name": f"{board_name} (Kanban)",
                "state": "active",
                "start_date": None,
                "end_date": None,
                "is_kanban": True
            },
            "issues_with_cycle_time": issues_with_cycle_time,
            "cycle_time_summary": self._summarize_sprint_cycle_time(
                issues_with_cycle_time
            )
        }

    def _analyze_sprint_cycle_time(self, sprint: Any, project: str) -> Dict[str, Any]:
        """Analyze cycle time for a single sprint."""
        self.logger.debug(
            f"Analyzing cycle time for sprint: {sprint.name} (ID: {sprint.id})"
        )

        from .sprint_service import SprintService
        sprint_service = SprintService(self.jira)
        sprint_info = sprint_service.get_sprint_info(sprint)

        # Get all issues for this sprint (not just bugs)
        issues = self.issue_service.get_issues_for_sprint(project, sprint.id)

        # Calculate cycle time for each issue using sprint-aware logic
        issues_with_cycle_time = []
        for issue in issues:
            cycle_time_data = self._calculate_issue_cycle_time_for_sprint(issue, sprint)
            if cycle_time_data:
                issues_with_cycle_time.append({
                    "issue": self.issue_service.get_issue_info(issue),
                    **cycle_time_data
                })

        return {
            "sprint_info": sprint_info,
            "issues_with_cycle_time": issues_with_cycle_time,
            "cycle_time_summary": self._summarize_sprint_cycle_time(
                issues_with_cycle_time
            )
        }

    def _calculate_issue_cycle_time_no_sprint(self, issue: Any) -> Optional[Dict[str, Any]]:
        """
        Calculate cycle time for an issue without sprint context (for Kanban boards).

        Logic:
        1. Get all changelogs for the issue
        2. Track time from first 'In Progress' to 'Done' across entire issue lifetime
        3. No sprint boundaries to consider

        Cycle time = time from first 'In Progress' status to 'Done'
        """
        try:
            # Get all issue changelogs
            all_changelog_entries = self.issue_service.get_issue_changelogs(issue.key)

            in_progress_time = None
            done_time = None
            lead_time_start = None

            # Parse creation time
            created_time = datetime.fromisoformat(
                issue.fields.created.replace("Z", "+00:00")
            )
            lead_time_start = created_time

            # Process all changelogs to find first in progress and done transitions
            for changelog in all_changelog_entries:
                entry_time = datetime.fromisoformat(
                    changelog.created.replace("Z", "+00:00")
                )

                for item in changelog.items:
                    if item.field == "status":
                        to_status = item.to_string or ""

                        # First transition to any "In Progress" status
                        in_progress_statuses = [
                            Status.get_status_name(Status.IN_PROGRESS.value).lower(),
                            Status.get_status_name(Status.REVIEW_AND_TESTING.value).lower()
                        ]
                        if not in_progress_time and any(status in to_status.lower() for status in in_progress_statuses):
                            in_progress_time = entry_time

                        # Transition to "Done" status
                        done_status_name = Status.get_status_name(Status.DONE.value).lower()
                        if done_status_name in to_status.lower():
                            done_time = entry_time

            # Calculate cycle time and lead time
            cycle_time = None
            lead_time = None

            if in_progress_time and done_time:
                cycle_time = done_time - in_progress_time

            if done_time:
                lead_time = done_time - lead_time_start

            # Calculate cycle time in days
            cycle_time_days = None
            if cycle_time:
                cycle_time_days = cycle_time.total_seconds() / 86400

            # Debug logging for unreasonable values
            if cycle_time_days and cycle_time_days > 365:
                self.logger.warning(
                    f"Unreasonably long cycle time for {issue.key}: {cycle_time_days:.1f} days. "
                    f"In Progress: {in_progress_time}, Done: {done_time}"
                )

            lead_time_days = None
            if lead_time:
                lead_time_days = lead_time.total_seconds() / 86400

            # Calculate status time breakdown during cycle time period
            status_time_breakdown = self._calculate_status_time_breakdown(
                all_changelog_entries, in_progress_time, done_time
            ) if in_progress_time and done_time else {}

            # Get issue type for bug vs task analysis
            issue_type = self._get_issue_type_category(issue)

            return {
                "cycle_time_days": cycle_time_days,
                "lead_time_days": lead_time_days,
                "cycle_time_hours": (cycle_time.total_seconds() / 3600
                                     if cycle_time else None),
                "lead_time_hours": (lead_time.total_seconds() / 3600
                                    if lead_time else None),
                "created_time": created_time,
                "in_progress_time": in_progress_time,
                "done_time": done_time,
                "status_transitions": len(all_changelog_entries),
                "cross_sprint_scenario": False,  # Not applicable for Kanban
                "status_time_breakdown": status_time_breakdown,
                "issue_type_category": issue_type,
                "sprint_context": None  # No sprint context for Kanban
            }

        except Exception as e:
            self.logger.error(
                f"Error calculating cycle time for Kanban issue {issue.key}: {e}"
            )
            return None

    def _calculate_issue_cycle_time_for_sprint(self, issue: Any, sprint: Any) -> Optional[Dict[str, Any]]:
        """
        Calculate sprint-aware cycle time for a single issue.

        Logic:
        1. Get all changelogs for the issue
        2. Filter changelogs to only include those within the sprint date range
        3. Track time from first 'In Progress' to 'Done' within the sprint
        4. If issue doesn't complete in sprint, handle cross-sprint scenarios

        Cycle time = time from first 'In Progress' status to 'Done' within sprint context
        """
        try:
            # Get all issue changelogs
            all_changelog_entries = self.issue_service.get_issue_changelogs(issue.key)

            # Filter changelogs to only include those within the sprint date range
            sprint_changelog_entries = self.issue_service.filter_changelogs_by_sprint_dates(
                all_changelog_entries, sprint
            )

            in_progress_time = None
            done_time = None
            lead_time_start = None
            cross_sprint_scenario = False

            # Parse creation time
            created_time = datetime.fromisoformat(
                issue.fields.created.replace("Z", "+00:00")
            )
            lead_time_start = created_time

            # Parse sprint dates for reference
            from dateutil.parser import isoparse
            sprint_start = isoparse(sprint.start_date)
            sprint_end = isoparse(sprint.end_date) if sprint.end_date else None

            # Check if issue was already in progress before this sprint
            # by looking at ALL changelogs, not just sprint-filtered ones
            in_progress_before_sprint = False
            for changelog in all_changelog_entries:
                entry_time = datetime.fromisoformat(
                    changelog.created.replace("Z", "+00:00")
                )

                # If this changelog is before sprint start
                if entry_time < sprint_start:
                    for item in changelog.items:
                        if item.field == "status":
                            to_status = item.to_string or ""
                            # If it moved to in progress before sprint (using proper status names)
                            in_progress_statuses = [
                                Status.get_status_name(Status.IN_PROGRESS.value).lower(),  # "in progress"
                                Status.get_status_name(Status.REVIEW_AND_TESTING.value).lower()  # "review and testing"
                            ]
                            if any(status in to_status.lower() for status in in_progress_statuses):
                                in_progress_before_sprint = True
                                in_progress_time = entry_time  # Use the actual first in progress time
                                cross_sprint_scenario = True
                                break

            # Process sprint-specific changelogs for transitions that happened during sprint
            for changelog in sprint_changelog_entries:
                entry_time = datetime.fromisoformat(
                    changelog.created.replace("Z", "+00:00")
                )

                for item in changelog.items:
                    if item.field == "status":
                        to_status = item.to_string or ""

                        # First transition to any "In Progress" status within sprint
                        # (only if not already in progress before sprint)
                        in_progress_statuses = [
                            Status.get_status_name(Status.IN_PROGRESS.value).lower(),  # "in progress"
                            Status.get_status_name(Status.REVIEW_AND_TESTING.value).lower()  # "review and testing"
                        ]
                        if (not in_progress_before_sprint and not in_progress_time and
                                any(status in to_status.lower() for status in in_progress_statuses)):
                            in_progress_time = entry_time

                        # Transition to "Done" status within sprint (using proper status name)
                        done_status_name = Status.get_status_name(Status.DONE.value).lower()  # "done"
                        if done_status_name in to_status.lower():
                            done_time = entry_time

            # If issue is currently done but we didn't find transition within sprint,
            # check if it was completed after sprint (cross-sprint scenario)
            current_status = issue.fields.status.name.lower()
            done_status_name = Status.get_status_name(Status.DONE.value).lower()  # "done"
            if not done_time and done_status_name in current_status:

                # Look for done transition in ALL changelogs (not just sprint-filtered)
                for changelog in all_changelog_entries:
                    entry_time = datetime.fromisoformat(
                        changelog.created.replace("Z", "+00:00")
                    )

                    # If this changelog is after sprint end (or during sprint we missed)
                    for item in changelog.items:
                        if item.field == "status":
                            to_status = item.to_string or ""
                            done_status_name = Status.get_status_name(Status.DONE.value).lower()  # "done"
                            if done_status_name in to_status.lower():
                                done_time = entry_time
                                if sprint_end and entry_time > sprint_end:
                                    cross_sprint_scenario = True
                                break

            # Calculate cycle time and lead time
            cycle_time = None
            lead_time = None

            if in_progress_time and done_time:
                cycle_time = done_time - in_progress_time

            if done_time:
                lead_time = done_time - lead_time_start

            # Calculate cycle time in days (more accurate)
            cycle_time_days = None
            if cycle_time:
                cycle_time_days = cycle_time.total_seconds() / 86400  # Convert to days

            # Debug logging for unreasonable values
            if cycle_time_days and cycle_time_days > 365:  # More than a year
                self.logger.warning(
                    f"Unreasonably long cycle time for {issue.key}: {cycle_time_days:.1f} days. "
                    f"In Progress: {in_progress_time}, Done: {done_time}, Cross-sprint: {cross_sprint_scenario}"
                )

            lead_time_days = None
            if lead_time:
                lead_time_days = lead_time.total_seconds() / 86400

            # Calculate status time breakdown during cycle time period
            status_time_breakdown = self._calculate_status_time_breakdown(
                all_changelog_entries, in_progress_time, done_time, sprint_start, sprint_end
            ) if in_progress_time and done_time else {}

            # Get issue type for bug vs task analysis
            issue_type = self._get_issue_type_category(issue)

            return {
                "cycle_time_days": cycle_time_days,
                "lead_time_days": lead_time_days,
                "cycle_time_hours": (cycle_time.total_seconds() / 3600
                                     if cycle_time else None),  # Keep for backwards compatibility
                "lead_time_hours": (lead_time.total_seconds() / 3600
                                    if lead_time else None),
                "created_time": created_time,
                "in_progress_time": in_progress_time,
                "done_time": done_time,
                "status_transitions": len(sprint_changelog_entries),
                "cross_sprint_scenario": cross_sprint_scenario,
                "status_time_breakdown": status_time_breakdown,
                "issue_type_category": issue_type,
                "sprint_context": {
                    "sprint_name": sprint.name,
                    "sprint_start": sprint_start,
                    "sprint_end": sprint_end
                }
            }

        except Exception as e:
            self.logger.error(
                f"Error calculating sprint-aware cycle time for issue {issue.key} in sprint {sprint.name}: {e}"
            )
            return None

    def _calculate_status_time_breakdown(
        self,
        changelog_entries: List[Any],
        in_progress_time: datetime,
        done_time: datetime,
        sprint_start: datetime = None,
        sprint_end: datetime = None
    ) -> Dict[str, float]:
        """Calculate time spent in each status during the cycle time period."""

        try:
            status_times = {}
            current_status = None
            current_status_start = in_progress_time

            # Sort changelogs by time to process in chronological order
            sorted_changelogs = sorted(changelog_entries,
                                     key=lambda x: datetime.fromisoformat(x.created.replace("Z", "+00:00")))

            for changelog in sorted_changelogs:
                entry_time = datetime.fromisoformat(changelog.created.replace("Z", "+00:00"))

                # Only process changelogs within the cycle time period
                if entry_time < in_progress_time or entry_time > done_time:
                    continue

                for item in changelog.items:
                    if item.field == "status" and item.to_string:
                        # Calculate time spent in previous status
                        if current_status and current_status_start:
                            time_in_status = (entry_time - current_status_start).total_seconds() / 86400  # Convert to days
                            status_times[current_status] = status_times.get(current_status, 0) + time_in_status

                        # Update current status
                        current_status = item.to_string
                        current_status_start = entry_time

            # Calculate time in final status until done
            if current_status and current_status_start:
                time_in_final_status = (done_time - current_status_start).total_seconds() / 86400
                status_times[current_status] = status_times.get(current_status, 0) + time_in_final_status

            return status_times

        except Exception as e:
            self.logger.error(f"Error calculating status time breakdown: {e}")
            return {}

    def _get_issue_type_category(self, issue: Issue) -> str:
        """Categorize issue as 'Bug' or 'Task' based on issue type."""

        try:
            # Access issue type name via the correct field path
            if hasattr(issue.fields, 'issue_type') and hasattr(issue.fields.issue_type, 'name'):
                issue_type = issue.fields.issue_type.name.lower()
            elif hasattr(issue.fields, 'issuetype') and hasattr(issue.fields.issuetype, 'name'):
                # Fallback to direct alias access
                issue_type = issue.fields.issuetype.name.lower()
            else:
                # Debug logging to understand the structure
                available_fields = dir(issue.fields) if hasattr(issue, 'fields') else []
                self.logger.debug(f"Could not access issue type for {issue.key}. Available fields: {[f for f in available_fields if not f.startswith('_')]}")
                return "Unknown"

            # Map various issue types to Bug or Task categories
            if any(bug_type in issue_type for bug_type in ['bug', 'defect', 'error', 'fault']):
                return "Bug"
            elif any(task_type in issue_type for task_type in ['task', 'story', 'feature', 'improvement', 'epic', 'subtask', 'sub-task']):
                return "Task"
            else:
                return "Other"

        except Exception as e:
            self.logger.error(f"Error determining issue type for {issue.key}: {e}")
            return "Unknown"

    def _calculate_overall_cycle_time_metrics(
        self,
        all_issues: List[Dict[str, Any]],
        collection_frequency: str = "sprint_wise"
    ) -> Dict[str, Any]:
        """Calculate overall cycle time metrics from all issues."""

        # Filter issues with valid cycle times (prioritize days)
        all_cycle_times_days = [
            issue["cycle_time_days"]
            for issue in all_issues
            if issue.get("cycle_time_days") is not None
        ]

        if not all_cycle_times_days:
            return {
                "metric_collection": {
                    "total_issues_analyzed": len(all_issues),
                    "date_range": self._calculate_date_range(all_issues),
                    "aggregate_display": "No valid cycle times found"
                },
                "average_cycle_time": {"value": 0, "unit": "days"},
                "longest_cycle_time": {"value": 0, "unit": "days"},
                "analysis": {
                    "bottlenecks": [],
                    "time_distribution": {},
                    "description": "No issues with valid cycle times found"
                },
                "improvement_steps": {
                    "immediate": ["Ensure issues transition through In Progress status"],
                    "long_term": ["Review workflow to capture cycle time data"],
                    "description": "No cycle time data available for analysis"
                },
                "additional_comments": {
                    "noteworthy_exceptions": [],
                    "context": [f"Analyzed {len(all_issues)} issues but none had valid cycle times"],
                    "description": "No cycle time data available"
                }
            }

        # Detect and separate outliers for more accurate statistics
        outlier_threshold = 30.0  # Issues with cycle time > 30 days are considered outliers
        outliers = []
        normal_cycle_times = []

        for issue in all_issues:
            cycle_time = issue.get("cycle_time_days")
            if cycle_time is not None:
                if cycle_time > outlier_threshold:
                    issue_key = issue["issue"]["key"]
                    outliers.append({
                        "issue": issue,
                        "cycle_time_days": cycle_time
                    })
                    self.logger.debug(
                        f"Detected outlier: {issue_key} with {cycle_time:.1f} days cycle time"
                    )
                else:
                    normal_cycle_times.append(cycle_time)

        # Use normal cycle times for statistics (excluding outliers)
        cycle_times_days = normal_cycle_times if normal_cycle_times else all_cycle_times_days

        self.logger.info(
            f"Cycle time analysis: {len(all_cycle_times_days)} total issues, "
            f"{len(outliers)} outliers (>{outlier_threshold} days), "
            f"{len(normal_cycle_times)} used for statistics"
        )

        # Calculate statistics (using days as primary unit, excluding outliers)
        avg_cycle_time_days = mean(cycle_times_days)
        max_cycle_time_days = max(cycle_times_days)

        # Find the longest issue from the NON-OUTLIER set
        longest_issue = None
        for issue in all_issues:
            cycle_time = issue.get("cycle_time_days")
            if cycle_time is not None and cycle_time == max_cycle_time_days and cycle_time <= 30.0:  # Ensure it's not an outlier
                longest_issue = {
                    "key": issue["issue"]["key"],
                    "summary": issue["issue"]["fields"]["summary"],
                    "cycle_time_days": max_cycle_time_days
                }
                break

        # Analyze bottlenecks and time distribution
        analysis_data = self._analyze_bottlenecks_and_distribution(all_issues)

        # Generate improvement steps
        improvement_steps = self._generate_improvement_recommendations(
            avg_cycle_time_days, max_cycle_time_days, analysis_data
        )

        # Determine date range
        date_range = self._calculate_date_range(all_issues)

        return {
            "metric_collection": {
                "total_issues_analyzed": len(cycle_times_days),
                "date_range": date_range,
                "aggregate_display": self._get_aggregate_display_format(collection_frequency)
            },
            "average_cycle_time": {
                "value": round(avg_cycle_time_days, 1),
                "unit": "days",
                "description": (f"Average time from 'In Progress' to 'Done' "
                                f"over {len(cycle_times_days)} issues")
            },
            "longest_cycle_time": {
                "value": round(max_cycle_time_days, 1),
                "unit": "days",
                "single_longest_issue": longest_issue,
                "description": (f"The single longest issue took "
                                f"{max_cycle_time_days:.1f} days")
            },
            "analysis": analysis_data,
            "improvement_steps": improvement_steps,
            "additional_comments": {
                "noteworthy_exceptions": self._identify_noteworthy_exceptions(
                    all_issues, outliers
                ),
                "context": [
                    f"Analysis based on {len(all_issues)} total issues from Jira",
                    f"Statistics calculated from {len(cycle_times_days)} issues (excluding {len(outliers)} outliers > 30 days)"
                ],
                "description": "Cycle time analysis with outlier detection and automated change detection"
            }
        }

    def _analyze_bottlenecks_and_distribution(
        self, all_issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze where tasks spend the most time and identify bottlenecks."""

        # Group by cycle time ranges
        time_buckets = {
            "< 1 day": 0,
            "1-3 days": 0,
            "3-7 days": 0,
            "1-2 weeks": 0,
            "> 2 weeks": 0
        }

        bottlenecks = []

        for issue in all_issues:
            cycle_time_days = issue.get("cycle_time_days")

            # Skip issues without valid cycle times
            if cycle_time_days is None:
                continue

            if cycle_time_days < 1:
                time_buckets["< 1 day"] += 1
            elif cycle_time_days <= 3:
                time_buckets["1-3 days"] += 1
            elif cycle_time_days <= 7:
                time_buckets["3-7 days"] += 1
            elif cycle_time_days <= 14:
                time_buckets["1-2 weeks"] += 1
            else:
                time_buckets["> 2 weeks"] += 1

                # Issues taking > 2 weeks are potential bottlenecks
                bottlenecks.append({
                    "issue_key": issue["issue"]["key"],
                    "cycle_time_days": cycle_time_days,
                    "summary": issue["issue"]["fields"]["summary"][:60] + "..."
                })

        return {
            "bottlenecks": bottlenecks[:5],  # Top 5 bottlenecks
            "time_distribution": time_buckets,
            "description": (f"Found {len(bottlenecks)} issues with cycle "
                            "times > 2 weeks")
        }

    def _generate_improvement_recommendations(
        self,
        avg_cycle_time_days: float,
        max_cycle_time_days: float,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate improvement recommendations based on metrics."""

        immediate = []
        long_term = []

        # Recommendations based on average cycle time (in days)
        if avg_cycle_time_days > 7:  # > 1 week
            immediate.append(
                "Review work-in-progress limits to reduce context switching"
            )
            immediate.append(
                "Identify and address current blockers in active issues"
            )

        if avg_cycle_time_days > 14:  # > 2 weeks
            immediate.append("Define clearer acceptance criteria upfront")
            long_term.append(
                "Consider breaking down larger tasks into smaller chunks"
            )

        # Recommendations based on longest cycle time
        if max_cycle_time_days > 21:  # > 3 weeks
            immediate.append(
                "Investigate external dependencies causing delays"
            )
            long_term.append("Establish SLAs with external teams")

        # Recommendations based on bottlenecks
        bottleneck_count = len(analysis_data.get("bottlenecks", []))
        if bottleneck_count > 2:
            immediate.append(
                "Address current long-running issues blocking flow"
            )
            long_term.append("Add dedicated QA person to reduce wait time")

        return {
            "immediate": (immediate if immediate else
                          ["Monitor current cycle times for trends"]),
            "long_term": (long_term if long_term else
                          ["Maintain current workflow efficiency"]),
            "description": "Recommendations based on current cycle time patterns"
        }

    def _identify_noteworthy_exceptions(
        self, all_issues: List[Dict[str, Any]], outliers: List[Dict[str, Any]] = None
    ) -> List[str]:
        """Identify noteworthy exceptions in the data, including outliers."""

        exceptions = []

        # Add outliers that were excluded from statistics
        if outliers:
            for outlier in outliers:
                issue_info = outlier["issue"]["issue"]
                cycle_time = outlier["cycle_time_days"]
                exceptions.append(
                    f"{issue_info['key']}: {cycle_time:.1f} days (outlier - excluded from stats)"
                )

        # If no outliers or need more exceptions, find high cycle time issues from normal range
        if len(exceptions) < 5:  # Show up to 5 exceptions
            normal_issues = [
                issue for issue in all_issues
                if issue.get("cycle_time_days") is not None and issue.get("cycle_time_days") <= 30.0
            ]

            if normal_issues:
                normal_cycle_times = [issue.get("cycle_time_days") for issue in normal_issues]
                avg_normal_cycle_time = mean(normal_cycle_times)

                for issue in normal_issues:
                    if len(exceptions) >= 5:  # Limit total exceptions
                        break
                    cycle_time = issue.get("cycle_time_days")
                    if cycle_time is not None and cycle_time > avg_normal_cycle_time * 2.5:  # 2.5x longer than normal average
                        exceptions.append(
                            f"{issue['issue']['key']}: {cycle_time:.1f} days "
                            f"({cycle_time/avg_normal_cycle_time:.1f}x normal average)"
                        )

        return exceptions[:5]  # Top 5 exceptions

    def _calculate_date_range(
        self, all_issues: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Calculate the date range covered by the analysis."""

        dates = []
        for issue in all_issues:
            if issue.get("created_time"):
                dates.append(issue["created_time"])
            if issue.get("done_time"):
                dates.append(issue["done_time"])

        if not dates:
            return None

        min_date = min(dates)
        max_date = max(dates)

        return (f"{min_date.strftime('%Y-%m-%d')} to "
                f"{max_date.strftime('%Y-%m-%d')}")

    def _summarize_sprint_cycle_time(
        self, issues_with_cycle_time: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize cycle time metrics for a sprint with outlier detection."""

        if not issues_with_cycle_time:
            return {"count": 0}

        all_cycle_times_days = [
            issue["cycle_time_days"]
            for issue in issues_with_cycle_time
            if issue.get("cycle_time_days") is not None
        ]

        if not all_cycle_times_days:
            return {
                "count": len(issues_with_cycle_time),
                "completed_count": 0
            }

        # Detect sprint-level outliers (same 30-day threshold)
        outlier_threshold = 30.0
        sprint_outliers = []
        normal_cycle_times = []

        for issue in issues_with_cycle_time:
            cycle_time = issue.get("cycle_time_days")
            if cycle_time is not None:
                if cycle_time > outlier_threshold:
                    sprint_outliers.append({
                        "issue_key": issue["issue"]["key"],
                        "cycle_time_days": cycle_time
                    })
                else:
                    normal_cycle_times.append(cycle_time)

        # Use normal cycle times for sprint statistics (excluding outliers)
        cycle_times_for_stats = normal_cycle_times if normal_cycle_times else all_cycle_times_days

        # Analyze status time breakdown
        status_analysis = self._analyze_sprint_status_breakdown(issues_with_cycle_time)

        # Analyze issue type breakdown (bugs vs tasks)
        type_analysis = self._analyze_sprint_type_breakdown(issues_with_cycle_time, outlier_threshold)

        # Get best/worst by issue type for this sprint
        best_worst_by_type = self._get_best_worst_by_issue_type(issues_with_cycle_time, outlier_threshold)

        return {
            "count": len(issues_with_cycle_time),
            "completed_count": len(all_cycle_times_days),
            "normal_completed_count": len(normal_cycle_times),
            "outlier_count": len(sprint_outliers),
            "outliers": sprint_outliers,  # Include outlier details
            "average_cycle_time_days": mean(cycle_times_for_stats),
            "median_cycle_time_days": median(cycle_times_for_stats),
            "max_cycle_time_days": max(cycle_times_for_stats),
            "min_cycle_time_days": min(cycle_times_for_stats),
            "status_time_analysis": status_analysis,
            "issue_type_breakdown": type_analysis,
            "best_worst_by_type": best_worst_by_type
        }

    def _get_best_worst_by_issue_type(
        self, issues_with_cycle_time: List[Dict[str, Any]], outlier_threshold: float
    ) -> Dict[str, Any]:
        """Get best (shortest) and worst (longest) cycle times by issue type for a sprint."""

        try:
            type_data = {"Bug": [], "Task": []}

            # Collect cycle times by type (exclude outliers)
            for issue in issues_with_cycle_time:
                issue_type = issue.get("issue_type_category", "Unknown")
                cycle_time = issue.get("cycle_time_days")

                if cycle_time is not None and cycle_time <= outlier_threshold:
                    if issue_type in type_data:
                        type_data[issue_type].append({
                            "issue_key": issue["issue"]["key"],
                            "cycle_time_days": cycle_time,
                            "summary": issue["issue"]["fields"]["summary"]
                        })

            result = {}

            # Find best/worst for each type
            for issue_type, issues in type_data.items():
                if issues:
                    sorted_issues = sorted(issues, key=lambda x: x["cycle_time_days"])

                    result[issue_type] = {
                        "best": {
                            "issue_key": sorted_issues[0]["issue_key"],
                            "cycle_time_days": round(sorted_issues[0]["cycle_time_days"], 1),
                            "summary": sorted_issues[0]["summary"][:50] + "..."
                        },
                        "worst": {
                            "issue_key": sorted_issues[-1]["issue_key"],
                            "cycle_time_days": round(sorted_issues[-1]["cycle_time_days"], 1),
                            "summary": sorted_issues[-1]["summary"][:50] + "..."
                        }
                    }

            return result

        except Exception as e:
            self.logger.error(f"Error getting best/worst by issue type: {e}")
            return {}

    def _get_overall_best_worst_by_type(self, all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get overall best and worst cycle times by issue type across all sprints."""

        try:
            outlier_threshold = 30.0
            type_data = {"Bug": [], "Task": []}

            # Collect all cycle times by type across all sprints (exclude outliers)
            for issue in all_issues:
                issue_type = issue.get("issue_type_category", "Unknown")
                cycle_time = issue.get("cycle_time_days")
                sprint_context = issue.get("sprint_context")

                if cycle_time is not None and cycle_time <= outlier_threshold:
                    if issue_type in type_data:
                        sprint_name = sprint_context.get("sprint_name") if sprint_context else "Unknown"
                        type_data[issue_type].append({
                            "issue_key": issue["issue"]["key"],
                            "cycle_time_days": cycle_time,
                            "summary": issue["issue"]["fields"]["summary"],
                            "sprint_name": sprint_name
                        })

            result = {}

            # Find overall best/worst for each type
            for issue_type, issues in type_data.items():
                if issues:
                    sorted_issues = sorted(issues, key=lambda x: x["cycle_time_days"])

                    result[issue_type] = {
                        "best": {
                            "issue_key": sorted_issues[0]["issue_key"],
                            "cycle_time_days": round(sorted_issues[0]["cycle_time_days"], 1),
                            "summary": sorted_issues[0]["summary"][:50] + "...",
                            "sprint": sorted_issues[0]["sprint_name"]
                        },
                        "worst": {
                            "issue_key": sorted_issues[-1]["issue_key"],
                            "cycle_time_days": round(sorted_issues[-1]["cycle_time_days"], 1),
                            "summary": sorted_issues[-1]["summary"][:50] + "...",
                            "sprint": sorted_issues[-1]["sprint_name"]
                        },
                        "total_count": len(issues)
                    }

            return result

        except Exception as e:
            self.logger.error(f"Error getting overall best/worst by issue type: {e}")
            return {}

    def _get_aggregate_display_format(self, collection_frequency: str) -> str:
        """Get the appropriate aggregate display format."""

        formats = {
            "sprint_wise": "X-Axis=Sprint, Y-Axis=Average Cycle Time In Days",
            "monthly": "X-Axis=Month, Y-Axis=Average Cycle Time In Days",
            "quarterly": "X-Axis=Quarter, Y-Axis=Average Cycle Time In Days"
        }

        return formats.get(collection_frequency, formats["sprint_wise"])

    def _analyze_sprint_status_breakdown(self, issues_with_cycle_time: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze time spent in each status across all issues in the sprint."""

        try:
            # Aggregate status times across all issues
            total_status_times = {}
            issues_with_status_data = 0

            for issue in issues_with_cycle_time:
                status_breakdown = issue.get("status_time_breakdown", {})
                if status_breakdown:
                    issues_with_status_data += 1
                    for status, time_days in status_breakdown.items():
                        total_status_times[status] = total_status_times.get(status, 0) + time_days

            if not total_status_times or issues_with_status_data == 0:
                return {"message": "No status time data available"}

            # Calculate average time per status
            avg_status_times = {
                status: time_total / issues_with_status_data
                for status, time_total in total_status_times.items()
            }

            # Find status where most time is spent
            longest_status = max(avg_status_times.items(), key=lambda x: x[1]) if avg_status_times else None

            return {
                "average_time_per_status": avg_status_times,
                "total_issues_analyzed": issues_with_status_data,
                "longest_status": {
                    "name": longest_status[0],
                    "average_days": round(longest_status[1], 2)
                } if longest_status else None,
                "status_distribution": {
                    status: f"{(time / sum(avg_status_times.values()) * 100):.1f}%"
                    for status, time in avg_status_times.items()
                } if avg_status_times else {}
            }

        except Exception as e:
            self.logger.error(f"Error analyzing sprint status breakdown: {e}")
            return {"error": str(e)}

    def _analyze_sprint_type_breakdown(self, issues_with_cycle_time: List[Dict[str, Any]], outlier_threshold: float) -> Dict[str, Any]:
        """Analyze cycle times separately for bugs vs tasks."""

        try:
            type_data = {"Bug": [], "Task": [], "Other": [], "Unknown": []}

            # Categorize issues by type and collect cycle times
            for issue in issues_with_cycle_time:
                issue_type = issue.get("issue_type_category", "Unknown")
                cycle_time = issue.get("cycle_time_days")

                if cycle_time is not None and cycle_time <= outlier_threshold:  # Exclude outliers
                    type_data[issue_type].append(cycle_time)

            # Calculate statistics for each type
            breakdown = {}
            for issue_type, cycle_times in type_data.items():
                if cycle_times:  # Only include types that have data
                    breakdown[issue_type] = {
                        "count": len(cycle_times),
                        "average_cycle_time_days": round(mean(cycle_times), 2),
                        "median_cycle_time_days": round(median(cycle_times), 2),
                        "max_cycle_time_days": round(max(cycle_times), 2),
                        "min_cycle_time_days": round(min(cycle_times), 2)
                    }

            return {
                "breakdown": breakdown,
                "summary": {
                    "total_bugs": len(type_data["Bug"]),
                    "total_tasks": len(type_data["Task"]),
                    "bug_avg": round(mean(type_data["Bug"]), 2) if type_data["Bug"] else 0,
                    "task_avg": round(mean(type_data["Task"]), 2) if type_data["Task"] else 0
                }
            }

        except Exception as e:
            self.logger.error(f"Error analyzing sprint type breakdown: {e}")
            return {"error": str(e)}

    def generate_cycle_time_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted cycle time report."""

        report = []
        report.append(
            f"\n=== Cycle Time Analysis Report for Project: "
            f"{results['project']} ==="
        )

        # Metric Collection Summary
        metric_info = results["metric_collection"]
        report.append(
            f"Collection Frequency: {results['collection_frequency']}"
        )
        report.append(
            f"Total Issues Analyzed: {metric_info['total_issues_analyzed']}"
        )
        if metric_info.get("date_range"):
            report.append(f"Date Range: {metric_info['date_range']}")
        report.append(f"Aggregate Display: {metric_info['aggregate_display']}")

        # Tool Information
        report.append(f"Tool: {results['tool']}")

        # Key Metrics
        avg_cycle = results["average_cycle_time"]
        report.append(
            f"\nAverage Cycle Time: {avg_cycle['value']} {avg_cycle['unit']}"
        )
        report.append(f"Description: {avg_cycle['description']}")

        longest_cycle = results["longest_cycle_time"]
        report.append(
            f"\nLongest Cycle Time: {longest_cycle['value']} "
            f"{longest_cycle['unit']}"
        )
        if longest_cycle.get("single_longest_issue"):
            issue = longest_cycle["single_longest_issue"]
            report.append(f"Longest Issue: {issue['key']} - {issue['summary']}")
        report.append(f"Description: {longest_cycle['description']}")

        # Analysis
        analysis = results["analysis"]
        report.append("\n=== Analysis ===")
        report.append(f"Description: {analysis['description']}")

        if analysis.get("time_distribution"):
            report.append("\nTime Distribution:")
            for range_name, count in analysis["time_distribution"].items():
                report.append(f"  {range_name}: {count} issues")

        if analysis.get("bottlenecks"):
            report.append(
                f"\nBottlenecks ({len(analysis['bottlenecks'])} issues > 2 weeks):"
            )
            for bottleneck in analysis["bottlenecks"]:
                report.append(
                    f"  {bottleneck['issue_key']}: "
                    f"{bottleneck['cycle_time_days']:.1f} days"
                )
                report.append(f"    {bottleneck['summary']}")

        # Improvement Steps
        improvements = results["improvement_steps"]
        report.append("\n=== Improvement Steps ===")
        report.append(f"Description: {improvements['description']}")

        if improvements.get("immediate"):
            report.append("\nImmediate Actions:")
            for step in improvements["immediate"]:
                report.append(f"  • {step}")

        if improvements.get("long_term"):
            report.append("\nLong-term Actions:")
            for step in improvements["long_term"]:
                report.append(f"  • {step}")

        # Additional Comments
        comments = results["additional_comments"]
        report.append("\n=== Additional Comments ===")
        report.append(f"Description: {comments['description']}")

        if comments.get("noteworthy_exceptions"):
            report.append("\nNoteworthy Exceptions:")
            for exception in comments["noteworthy_exceptions"]:
                report.append(f"  • {exception}")

        if comments.get("context"):
            report.append("\nContext:")
            for context in comments["context"]:
                report.append(f"  • {context}")

        # Overall Best/Worst by Issue Type across all sprints
        if results.get("overall_best_worst"):
            overall_bw = results["overall_best_worst"]
            report.append("\n=== Overall Best & Worst Cycle Times (Across All Sprints) ===")

            for issue_type, data in overall_bw.items():
                report.append(f"\n{issue_type}s ({data['total_count']} total):")

                best = data["best"]
                report.append(
                    f"  Best (Fastest): {best['issue_key']} - {best['cycle_time_days']} days"
                )
                report.append(f"    Sprint: {best['sprint']}")
                report.append(f"    Summary: {best['summary']}")

                worst = data["worst"]
                report.append(
                    f"  Worst (Slowest): {worst['issue_key']} - {worst['cycle_time_days']} days"
                )
                report.append(f"    Sprint: {worst['sprint']}")
                report.append(f"    Summary: {worst['summary']}")

        # Board-level details
        if results.get("boards"):
            report.append("\n=== Board Details ===")
            for board_result in results["boards"]:
                board_info = board_result["board_info"]
                report.append(
                    f"\nBoard: {board_info['name']} (ID: {board_info['id']})"
                )

                for sprint_result in board_result["sprints"]:
                    sprint_info = sprint_result["sprint_info"]
                    summary = sprint_result["cycle_time_summary"]

                    report.append(
                        f"\n  Sprint: {sprint_info['name']} "
                        f"({sprint_info['state']})"
                    )
                    report.append(f"    Total Issues: {summary.get('count', 0)}")
                    report.append(
                        f"    Completed Issues: {summary.get('completed_count', 0)}"
                    )

                    # Show outlier information for this sprint
                    outlier_count = summary.get('outlier_count', 0)
                    normal_count = summary.get('normal_completed_count', 0)
                    if outlier_count > 0:
                        report.append(f"    Outliers (>30 days): {outlier_count}")
                        report.append(f"    Normal Issues: {normal_count}")

                        # List sprint outliers
                        outliers = summary.get('outliers', [])
                        for outlier in outliers:
                            report.append(
                                f"      • {outlier['issue_key']}: {outlier['cycle_time_days']:.1f} days"
                            )

                    if summary.get("normal_completed_count", 0) > 0:
                        avg_days = summary.get('average_cycle_time_days', 0)
                        median_days = summary.get('median_cycle_time_days', 0)
                        min_days = summary.get('min_cycle_time_days', 0)
                        max_days = summary.get('max_cycle_time_days', 0)

                        stats_label = "Stats (excluding outliers)" if outlier_count > 0 else "Stats"
                        report.append(f"    {stats_label}:")
                        report.append(
                            f"      Average Cycle Time: {avg_days:.1f} days"
                        )
                        report.append(
                            f"      Median Cycle Time: {median_days:.1f} days"
                        )
                        report.append(
                            f"      Range: {min_days:.1f} - {max_days:.1f} days"
                        )

                    # Add status time analysis
                    status_analysis = summary.get('status_time_analysis', {})
                    if status_analysis and not status_analysis.get('error') and not status_analysis.get('message'):
                        report.append("    Status Time Analysis:")
                        longest_status = status_analysis.get('longest_status')
                        if longest_status:
                            report.append(
                                f"      Most time spent in: {longest_status['name']} "
                                f"({longest_status['average_days']} days avg)"
                            )

                        status_dist = status_analysis.get('status_distribution', {})
                        if status_dist:
                            report.append("      Status Time Distribution:")
                            for status, percentage in status_dist.items():
                                avg_time = status_analysis.get('average_time_per_status', {}).get(status, 0)
                                report.append(f"        {status}: {percentage} ({avg_time:.1f} days avg)")

                    # Add issue type breakdown
                    type_breakdown = summary.get('issue_type_breakdown', {})
                    if type_breakdown and not type_breakdown.get('error'):
                        type_summary = type_breakdown.get('summary', {})
                        if type_summary.get('total_bugs') > 0 or type_summary.get('total_tasks') > 0:
                            report.append("    Issue Type Breakdown:")

                            if type_summary.get('total_bugs') > 0:
                                report.append(
                                    f"      Bugs: {type_summary['total_bugs']} issues, "
                                    f"avg {type_summary['bug_avg']} days"
                                )

                            if type_summary.get('total_tasks') > 0:
                                report.append(
                                    f"      Tasks: {type_summary['total_tasks']} issues, "
                                    f"avg {type_summary['task_avg']} days"
                                )

                            # Show detailed breakdown if available
                            breakdown = type_breakdown.get('breakdown', {})
                            if len(breakdown) > 0:
                                report.append("      Detailed Breakdown:")
                                for issue_type, stats in breakdown.items():
                                    if stats['count'] > 0:
                                        report.append(
                                            f"        {issue_type}: {stats['count']} issues, "
                                            f"avg {stats['average_cycle_time_days']} days "
                                            f"(range: {stats['min_cycle_time_days']}-{stats['max_cycle_time_days']})"
                                        )

                    # Add best/worst by issue type for this sprint
                    best_worst = summary.get('best_worst_by_type', {})
                    if best_worst:
                        report.append("    Best & Worst Cycle Times in This Sprint:")

                        for issue_type, data in best_worst.items():
                            report.append(f"      {issue_type}s:")

                            best = data["best"]
                            report.append(
                                f"        Best: {best['issue_key']} - {best['cycle_time_days']} days"
                            )
                            report.append(f"          {best['summary']}")

                            worst = data["worst"]
                            report.append(
                                f"        Worst: {worst['issue_key']} - {worst['cycle_time_days']} days"
                            )
                            report.append(f"          {worst['summary']}")

        return "\n".join(report)