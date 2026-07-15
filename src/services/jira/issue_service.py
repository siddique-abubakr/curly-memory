from datetime import timedelta
from dateutil.parser import isoparse
from collections import defaultdict, Counter
from statistics import median, quantiles
from typing import Dict, List, Optional, Tuple

from core.logger import Logger
from core.enums import WIPLabels, Status
from services.jira.models import Issue
from services.jira.models.sprint import Sprint
from services.jira.models.tracking import Changelog, ChangelogItem


class IssueService:
    """Service class for handling issue-related operations."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()

    def get_normalized_status_id(self, changelog_item: ChangelogItem) -> Optional[str]:
        """Get normalized status ID, preferring ID over string."""
        return changelog_item.from_id or changelog_item.from_string

    def get_normalized_status_to_id(self, changelog_item: ChangelogItem) -> Optional[str]:
        """Get normalized status TO ID, preferring ID over string."""
        return changelog_item.to_id or changelog_item.to_string

    def get_done_bugs_for_sprint(self, project: str, sprint_id: int) -> list[Issue]:
        """Get all done bugs for a specific sprint."""
        try:
            jql = (
                f"project = {project} AND "
                f"sprint = {sprint_id} AND "
                f"type = Bug AND status = Done"
            )
            issues = self.jira.search_issues(jql)
            self.logger.debug(f"Found {len(issues)} done bugs for sprint {sprint_id}")
            issues = [Issue(**issue.raw) for issue in issues]
            return issues
        except Exception as e:
            self.logger.error(f"Error fetching issues for sprint {sprint_id}: {e}")
            return []
    
    def get_bugs_for_sprint(self, project: str, sprint_id: int) -> list[Issue]:
        """Get all done bugs for a specific sprint."""
        try:
            jql = (
                f"project = {project} AND "
                f"sprint = {sprint_id} AND "
                f"type = Bug"
            )
            issues = self.jira.search_issues(jql)
            self.logger.debug(f"Found {len(issues)} bugs for sprint {sprint_id}")
            issues = [Issue(**issue.raw) for issue in issues]
            return issues
        except Exception as e:
            self.logger.error(f"Error fetching issues for sprint {sprint_id}: {e}")
            return []

    def get_issues_for_sprint(self, project: str, sprint_id: int) -> list[Issue]:
        """Get all done bugs for a specific sprint."""
        try:
            jql = f"project = {project} AND sprint = {sprint_id}"
            issues = self.jira.search_issues(jql)
            self.logger.debug(f"Found {len(issues)} issues for sprint {sprint_id}")
            issues = [Issue(**issue.raw) for issue in issues]
            return issues
        except Exception as e:
            self.logger.error(f"Error fetching issues for sprint {sprint_id}: {e}")
            return []

    def get_all_issues_for_board(self, project: str, board_id: int, date_filter: dict = None) -> list[Issue]:
        """Get all issues for a board (including Kanban boards without sprints).

        Args:
            project: Project key
            board_id: Board ID
            date_filter: Optional date filter with 'start_date' and 'end_date'

        Returns:
            List of issues for the board
        """
        try:
            # Use Jira Agile API to get all issues from a board
            # This works for both Scrum and Kanban boards
            self.logger.debug(f"Fetching issues for board {board_id} using Jira Agile API")

            # Build JQL for date filtering
            jql = None
            if date_filter and date_filter.get("enabled"):
                jql_parts = []
                start_date = date_filter.get("start_date")
                end_date = date_filter.get("end_date")

                if start_date:
                    start_str = start_date.strftime("%Y-%m-%d")
                    jql_parts.append(f"created >= '{start_str}'")

                if end_date:
                    end_str = end_date.strftime("%Y-%m-%d")
                    jql_parts.append(f"created <= '{end_str}'")

                jql = " AND ".join(jql_parts) if jql_parts else None

            # Use Agile API endpoint: GET /rest/agile/1.0/board/{boardId}/issue
            # The python-jira library doesn't have a direct method, so we use search_issues
            # with the internal board filtering that happens via the API

            # Get board to find its filter
            board = self.jira.boards(board_id)

            # Try to get the board's filter/configuration
            if hasattr(board, 'filter') and board.filter:
                # Board has a filter, get issues using that filter
                filter_id = board.filter.id if hasattr(board.filter, 'id') else None
                if filter_id:
                    board_jql = f"filter = {filter_id}"
                    if jql:
                        board_jql = f"({board_jql}) AND ({jql})"

                    issues = self.jira.search_issues(board_jql, maxResults=1000)
                    self.logger.debug(f"Found {len(issues)} issues for board {board_id} using filter {filter_id}")
                else:
                    # No filter ID, fall back to project
                    board_jql = f"project = {project}"
                    if jql:
                        board_jql = f"{board_jql} AND {jql}"

                    issues = self.jira.search_issues(board_jql, maxResults=1000)
                    self.logger.debug(f"Found {len(issues)} issues for project {project}")
            else:
                # Board has no filter, use project-based query
                board_jql = f"project = {project}"
                if jql:
                    board_jql = f"{board_jql} AND {jql}"

                issues = self.jira.search_issues(board_jql, maxResults=1000)
                self.logger.debug(f"Found {len(issues)} issues for project {project}")

            issues = [Issue(**issue.raw) for issue in issues]
            return issues

        except Exception as e:
            self.logger.error(f"Error fetching issues for board {board_id}: {e}")
            # Fallback to simple project query
            try:
                jql = f"project = {project}"
                if date_filter and date_filter.get("enabled"):
                    start_date = date_filter.get("start_date")
                    end_date = date_filter.get("end_date")

                    if start_date:
                        start_str = start_date.strftime("%Y-%m-%d")
                        jql += f" AND created >= '{start_str}'"

                    if end_date:
                        end_str = end_date.strftime("%Y-%m-%d")
                        jql += f" AND created <= '{end_str}'"

                issues = self.jira.search_issues(jql, maxResults=1000)
                self.logger.debug(f"Found {len(issues)} issues for project {project} (fallback)")
                issues = [Issue(**issue.raw) for issue in issues]
                return issues
            except Exception as fallback_error:
                self.logger.error(f"Error in fallback query for board {board_id}: {fallback_error}")
                return []

    def get_issue_changelogs(self, issue_key: str) -> list[Changelog]:
        """Get issue changelog/history"""
        try:
            changelogs = self.jira.changelogs(issue_key)
            changelogs = [Changelog(**changelog.raw) for changelog in changelogs]
            return changelogs
        except Exception as e:
            self.logger.error(f"Error fetching changelogs for issue {issue_key}\n {e}")
            return []

    def filter_status_changelogs(self, changelogs: list[Changelog]) -> list[Changelog]:
        """Filter changelogs for field type status"""
        return [
            changelog
            for changelog in changelogs
            if any(item.field_id == "status" for item in changelog.items)
        ]

    def filter_changelogs_by_sprint_dates(
        self, changelogs: list[Changelog], sprint: Sprint
    ) -> list[Changelog]:
        """Filter changelogs to only include those within the sprint date range"""
        try:
            sprint_start = isoparse(sprint.start_date)
            sprint_end = isoparse(sprint.end_date) if sprint.end_date else None

            filtered_changelogs = []
            for changelog in changelogs:
                changelog_date = isoparse(changelog.created)

                # Include changelog if it's within sprint date range
                if changelog_date >= sprint_start:
                    if sprint_end is None or changelog_date <= sprint_end:
                        filtered_changelogs.append(changelog)

            return filtered_changelogs
        except Exception as e:
            self.logger.error(f"Error filtering changelogs by sprint dates: {e}")
            return changelogs  # Return original list if filtering fails

    def group_changelogs_by_from_status(
        self, changelogs: list[Changelog]
    ) -> dict[str, list[Changelog]]:
        """Group changelogs based on the status the ticket was in before change"""
        groups = defaultdict(list)
        try:
            for cl in changelogs:
                status_item = next(
                    (it for it in cl.items if it.field_id == "status"),
                    None,
                )
                if not status_item:
                    continue
                from_status = self.get_normalized_status_id(status_item)
                if from_status is None:
                    continue
                groups[from_status].append(cl)
        except Exception as e:
            self.logger.error(f"Error while grouping changelogs by status {e}")
        return dict(groups)

    def calculate_time_per_status(
        self, status_changelogs: list[Changelog], issue: Issue = None
    ) -> dict[str, timedelta]:
        """Calculate the time in status including final status period"""
        status_deltas: dict[str, timedelta] = defaultdict(timedelta)
        try:
            if not status_changelogs:
                return status_deltas

            sorted_changelogs = sorted(
                status_changelogs, key=lambda c: isoparse(c.created)
            )

            # Calculate time between consecutive status changes
            for c in range(len(sorted_changelogs) - 1):
                status_item: ChangelogItem = next(
                    (
                        it
                        for it in sorted_changelogs[c].items
                        if it.field_id == "status"
                    ),
                    None,
                )
                if not status_item:
                    continue

                from_status: str = self.get_normalized_status_id(status_item)
                if not from_status:
                    continue

                status_deltas[from_status] += isoparse(
                    sorted_changelogs[c + 1].created
                ) - isoparse(sorted_changelogs[c].created)

            # Handle the final status period if issue is provided
            if issue and len(sorted_changelogs) > 0:
                # Get the final status from the last changelog
                last_changelog = sorted_changelogs[-1]
                last_status_item = next(
                    (
                        it
                        for it in last_changelog.items
                        if it.field_id == "status"
                    ),
                    None,
                )

                if last_status_item:
                    final_status = self.get_normalized_status_to_id(last_status_item)
                    if final_status:
                        # Calculate time from last status change to issue update time
                        last_change_time = isoparse(last_changelog.created)
                        issue_end_time = isoparse(issue.fields.updated)
                        final_status_duration = issue_end_time - last_change_time

                        if final_status_duration.total_seconds() > 0:
                            status_deltas[final_status] += final_status_duration

        except Exception as e:
            self.logger.error(f"Error while calculating time in status for issue {e}")
        return status_deltas

    def get_avg_time_per_status(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, timedelta]:
        """Returns average time in status for the tickets of a sprint.
        If sprint is provided, only considers changelogs within the sprint
        date range."""
        all_status_times = defaultdict(list)

        for issue in issues:
            try:
                # Get all changelogs for the issue
                all_changelogs = self.get_issue_changelogs(issue.key)

                # Filter by sprint dates if sprint is provided
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(
                        all_changelogs, sprint
                    )

                # Filter for status changelogs only
                status_changelogs = self.filter_status_changelogs(all_changelogs)
                issue_status_times = self.calculate_time_per_status(status_changelogs, issue)

                # Collect times for each status across all issues
                for status, time_spent in issue_status_times.items():
                    all_status_times[status].append(time_spent)

            except Exception as e:
                self.logger.error(
                    f"Error processing issue {issue.key} for time per status: {e}"
                )

        # Calculate average time per status
        avg_status_times = {}
        for status, times in all_status_times.items():
            if times:
                # Calculate average by summing all timedeltas and dividing by count
                total_time = sum(times, timedelta())
                avg_status_times[status] = total_time / len(times)

        return avg_status_times

    def get_max_age_per_status(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, dict]:
        """Returns the ticket with max age in each status for a sprint."""
        max_age_per_status = {}

        for issue in issues:
            try:
                # Get all changelogs for the issue
                all_changelogs = self.get_issue_changelogs(issue.key)

                # Filter by sprint dates if sprint is provided
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(
                        all_changelogs, sprint
                    )

                # Filter for status changelogs only
                status_changelogs = self.filter_status_changelogs(all_changelogs)
                issue_status_times = self.calculate_time_per_status(status_changelogs, issue)

                # Check if this issue has the max time for each status
                for status, time_spent in issue_status_times.items():
                    if status not in max_age_per_status or time_spent > max_age_per_status[status]["duration"]:
                        max_age_per_status[status] = {
                            "issue_key": issue.key,
                            "issue_summary": issue.fields.summary,
                            "duration": time_spent,
                            "duration_days": time_spent.days
                        }

            except Exception as e:
                self.logger.error(
                    f"Error processing issue {issue.key} for max age per status: {e}"
                )

        return max_age_per_status

    def get_median_time_per_status(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, timedelta]:
        """Returns median time in status for the tickets of a sprint."""
        all_status_times = defaultdict(list)

        for issue in issues:
            try:
                all_changelogs = self.get_issue_changelogs(issue.key)
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(all_changelogs, sprint)

                status_changelogs = self.filter_status_changelogs(all_changelogs)
                issue_status_times = self.calculate_time_per_status(status_changelogs, issue)

                for status, time_spent in issue_status_times.items():
                    all_status_times[status].append(time_spent)

            except Exception as e:
                self.logger.error(f"Error processing issue {issue.key} for median time per status: {e}")

        median_status_times = {}
        for status, times in all_status_times.items():
            if times:
                median_status_times[status] = timedelta(seconds=median([t.total_seconds() for t in times]))

        return median_status_times

    def get_percentile_time_per_status(
        self, issues: list[Issue], sprint: Sprint = None, percentile: int = 90
    ) -> dict[str, timedelta]:
        """Returns specified percentile time in status for the tickets of a sprint."""
        all_status_times = defaultdict(list)

        for issue in issues:
            try:
                all_changelogs = self.get_issue_changelogs(issue.key)
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(all_changelogs, sprint)

                status_changelogs = self.filter_status_changelogs(all_changelogs)
                issue_status_times = self.calculate_time_per_status(status_changelogs, issue)

                for status, time_spent in issue_status_times.items():
                    all_status_times[status].append(time_spent)

            except Exception as e:
                self.logger.error(f"Error processing issue {issue.key} for percentile time per status: {e}")

        percentile_status_times = {}
        for status, times in all_status_times.items():
            if times:
                time_seconds = [t.total_seconds() for t in times]
                # Use quantiles to get the specified percentile
                try:
                    percentiles = quantiles(time_seconds, n=100)
                    percentile_index = min(percentile - 1, len(percentiles) - 1)
                    percentile_status_times[status] = timedelta(seconds=percentiles[percentile_index])
                except:
                    # Fallback for small datasets
                    sorted_times = sorted(time_seconds)
                    index = int(len(sorted_times) * percentile / 100.0)
                    if index >= len(sorted_times):
                        index = len(sorted_times) - 1
                    percentile_status_times[status] = timedelta(seconds=sorted_times[index])

        return percentile_status_times

    def analyze_status_transitions(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, any]:
        """Analyze status transition patterns for issues in a sprint."""
        transitions = defaultdict(int)  # (from_status, to_status) -> count
        transition_times = defaultdict(list)  # (from_status, to_status) -> [durations]
        status_sequence_patterns = Counter()  # Full transition sequences

        for issue in issues:
            try:
                all_changelogs = self.get_issue_changelogs(issue.key)
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(all_changelogs, sprint)

                status_changelogs = self.filter_status_changelogs(all_changelogs)
                if not status_changelogs:
                    continue

                sorted_changelogs = sorted(status_changelogs, key=lambda c: isoparse(c.created))

                # Track transition sequence for this issue
                status_sequence = []

                # Process consecutive status changes
                for i in range(len(sorted_changelogs)):
                    current_changelog = sorted_changelogs[i]
                    status_item = next(
                        (it for it in current_changelog.items if it.field_id == "status"), None
                    )
                    if not status_item:
                        continue

                    from_status = self.get_normalized_status_id(status_item)
                    to_status = self.get_normalized_status_to_id(status_item)

                    if from_status and to_status:
                        # Add to sequence
                        if not status_sequence or status_sequence[-1] != from_status:
                            status_sequence.append(from_status)
                        status_sequence.append(to_status)

                        # Count transition
                        transition_key = (from_status, to_status)
                        transitions[transition_key] += 1

                        # Calculate transition time if we have next status change
                        if i < len(sorted_changelogs) - 1:
                            next_changelog = sorted_changelogs[i + 1]
                            transition_duration = isoparse(next_changelog.created) - isoparse(current_changelog.created)
                            transition_times[transition_key].append(transition_duration)

                # Store the full sequence pattern
                if status_sequence:
                    sequence_key = " → ".join([Status.get_status_name(s) for s in status_sequence])
                    status_sequence_patterns[sequence_key] += 1

            except Exception as e:
                self.logger.error(f"Error analyzing transitions for issue {issue.key}: {e}")

        # Calculate average transition times
        avg_transition_times = {}
        for transition_key, durations in transition_times.items():
            if durations:
                avg_duration = sum(durations, timedelta()) / len(durations)
                avg_transition_times[transition_key] = avg_duration

        return {
            "total_transitions": sum(transitions.values()),
            "transition_counts": dict(transitions),
            "average_transition_times": avg_transition_times,
            "common_sequences": dict(status_sequence_patterns.most_common(10)),
            "unique_sequences": len(status_sequence_patterns)
        }

    def calculate_cycle_times(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, any]:
        """Calculate end-to-end cycle times and lead times."""
        cycle_times = []
        lead_times = []
        cycle_time_details = []

        for issue in issues:
            try:
                all_changelogs = self.get_issue_changelogs(issue.key)
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(all_changelogs, sprint)

                status_changelogs = self.filter_status_changelogs(all_changelogs)
                if not status_changelogs:
                    continue

                sorted_changelogs = sorted(status_changelogs, key=lambda c: isoparse(c.created))

                # Find first "In Progress" and last "Done" status
                first_in_progress = None
                last_done = None

                for changelog in sorted_changelogs:
                    status_item = next(
                        (it for it in changelog.items if it.field_id == "status"), None
                    )
                    if not status_item:
                        continue

                    to_status = self.get_normalized_status_to_id(status_item)
                    to_status_name = Status.get_status_name(to_status) if to_status else ""

                    # Mark first time entering "In Progress"
                    if not first_in_progress and "In Progress" in to_status_name:
                        first_in_progress = isoparse(changelog.created)

                    # Mark last time entering "Done"
                    if "Done" in to_status_name:
                        last_done = isoparse(changelog.created)

                # Calculate cycle time (In Progress to Done)
                if first_in_progress and last_done and last_done > first_in_progress:
                    cycle_time = last_done - first_in_progress
                    cycle_times.append(cycle_time)

                    cycle_time_details.append({
                        "issue_key": issue.key,
                        "issue_summary": issue.fields.summary,
                        "cycle_time_days": cycle_time.days,
                        "start_date": first_in_progress.isoformat(),
                        "end_date": last_done.isoformat()
                    })

                # Calculate lead time (Created to Done)
                if last_done:
                    created_date = isoparse(issue.fields.created)
                    lead_time = last_done - created_date
                    lead_times.append(lead_time)

            except Exception as e:
                self.logger.error(f"Error calculating cycle time for issue {issue.key}: {e}")

        # Calculate statistics
        cycle_time_stats = {}
        if cycle_times:
            cycle_seconds = [ct.total_seconds() for ct in cycle_times]
            cycle_time_stats = {
                "count": len(cycle_times),
                "average_days": sum(cycle_times, timedelta()).total_seconds() / len(cycle_times) / 86400,
                "median_days": median(cycle_seconds) / 86400,
                "min_days": min(cycle_seconds) / 86400,
                "max_days": max(cycle_seconds) / 86400
            }

        lead_time_stats = {}
        if lead_times:
            lead_seconds = [lt.total_seconds() for lt in lead_times]
            lead_time_stats = {
                "count": len(lead_times),
                "average_days": sum(lead_times, timedelta()).total_seconds() / len(lead_times) / 86400,
                "median_days": median(lead_seconds) / 86400,
                "min_days": min(lead_seconds) / 86400,
                "max_days": max(lead_seconds) / 86400
            }

        return {
            "cycle_time_stats": cycle_time_stats,
            "lead_time_stats": lead_time_stats,
            "cycle_time_details": sorted(cycle_time_details, key=lambda x: x["cycle_time_days"], reverse=True)
        }

    def analyze_workflow_bottlenecks(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, any]:
        """Identify workflow bottlenecks based on time spent in each status."""
        status_time_data = defaultdict(list)
        total_time_per_issue = {}

        for issue in issues:
            try:
                all_changelogs = self.get_issue_changelogs(issue.key)
                if sprint:
                    all_changelogs = self.filter_changelogs_by_sprint_dates(all_changelogs, sprint)

                status_changelogs = self.filter_status_changelogs(all_changelogs)
                issue_status_times = self.calculate_time_per_status(status_changelogs, issue)

                issue_total_time = sum(issue_status_times.values(), timedelta())
                if issue_total_time.total_seconds() > 0:
                    total_time_per_issue[issue.key] = issue_total_time

                for status, time_spent in issue_status_times.items():
                    status_time_data[status].append({
                        "issue_key": issue.key,
                        "time_spent": time_spent,
                        "days": time_spent.days
                    })

            except Exception as e:
                self.logger.error(f"Error analyzing bottlenecks for issue {issue.key}: {e}")

        # Calculate bottleneck metrics
        bottlenecks = {}
        for status, time_data in status_time_data.items():
            if not time_data:
                continue

            times = [item["time_spent"] for item in time_data]
            time_seconds = [t.total_seconds() for t in times]

            status_name = Status.get_status_name(status)
            bottlenecks[status_name] = {
                "issue_count": len(time_data),
                "total_time_days": sum(times, timedelta()).days,
                "average_time_days": sum(times, timedelta()).total_seconds() / len(times) / 86400,
                "median_time_days": median(time_seconds) / 86400,
                "max_time_days": max(time_seconds) / 86400,
                "longest_issue": max(time_data, key=lambda x: x["time_spent"])["issue_key"],
                "efficiency_score": self._calculate_efficiency_score(times)
            }

        # Rank by average time (potential bottlenecks)
        sorted_bottlenecks = dict(sorted(
            bottlenecks.items(),
            key=lambda x: x[1]["average_time_days"],
            reverse=True
        ))

        return {
            "bottleneck_analysis": sorted_bottlenecks,
            "top_bottlenecks": list(sorted_bottlenecks.keys())[:3],
            "total_issues_analyzed": len(total_time_per_issue),
            "workflow_efficiency": self._calculate_workflow_efficiency(bottlenecks)
        }

    def _calculate_efficiency_score(self, times: list[timedelta]) -> float:
        """Calculate efficiency score based on time variance (lower is better)."""
        if len(times) < 2:
            return 1.0

        time_seconds = [t.total_seconds() for t in times]
        avg_time = sum(time_seconds) / len(time_seconds)

        if avg_time == 0:
            return 1.0

        variance = sum((t - avg_time) ** 2 for t in time_seconds) / len(time_seconds)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / avg_time

        # Lower coefficient of variation = higher efficiency (0-1 scale)
        return max(0, 1 - min(coefficient_of_variation, 1))

    def _calculate_workflow_efficiency(self, bottlenecks: dict) -> dict:
        """Calculate overall workflow efficiency metrics."""
        if not bottlenecks:
            return {"overall_score": 0, "areas_for_improvement": []}

        efficiency_scores = [data["efficiency_score"] for data in bottlenecks.values()]
        overall_efficiency = sum(efficiency_scores) / len(efficiency_scores)

        # Identify areas for improvement (low efficiency scores)
        improvement_areas = [
            status for status, data in bottlenecks.items()
            if data["efficiency_score"] < 0.7
        ]

        return {
            "overall_score": overall_efficiency,
            "areas_for_improvement": improvement_areas,
            "most_efficient_status": max(bottlenecks.keys(), key=lambda k: bottlenecks[k]["efficiency_score"]) if bottlenecks else None,
            "least_efficient_status": min(bottlenecks.keys(), key=lambda k: bottlenecks[k]["efficiency_score"]) if bottlenecks else None
        }

    def get_comprehensive_status_metrics(
        self, issues: list[Issue], sprint: Sprint = None
    ) -> dict[str, any]:
        """Get comprehensive status metrics including all analysis types."""
        return {
            'average_times': self.get_avg_time_per_status(issues, sprint),
            'median_times': self.get_median_time_per_status(issues, sprint),
            'percentile_90_times': self.get_percentile_time_per_status(issues, sprint, 90),
            'max_age_per_status': self.get_max_age_per_status(issues, sprint),
            'status_transitions': self.analyze_status_transitions(issues, sprint),
            'cycle_time_analysis': self.calculate_cycle_times(issues, sprint),
            'bottleneck_analysis': self.analyze_workflow_bottlenecks(issues, sprint)
        }

    def get_issue_info(self, issue: Issue) -> dict[str, any]:
        """Get formatted issue information."""
        try:
            return issue.model_dump()
        except Exception as e:
            self.logger.error(f"Error getting issue info: {e}")
            return {}

    def calculate_resolution_metrics(self, issues: list[Issue]) -> dict[str, any]:
        """Calculate resolution time metrics for a list of issues."""
        if not issues:
            return {"count": 0, "avg_resolution_days": 0, "max_resolution_days": 0}

        resolution_times = []
        for issue in issues:
            try:
                # Validate issue object
                if (
                    not hasattr(issue, "fields")
                    or not hasattr(issue.fields, "created")
                    or not hasattr(issue.fields, "updated")
                ):
                    self.logger.debug(
                        f"Skipping issue without required fields: {
                            getattr(issue, 'key', 'Unknown')
                        }"
                    )
                    continue

                resolution_times.append(issue.resolution_time_days)
            except Exception as e:
                self.logger.error(
                    f"Error calculating resolution time for issue {
                        getattr(issue, 'key', 'Unknown')
                    }: {e}"
                )

        if not resolution_times:
            return {"count": 0, "avg_resolution_days": 0, "max_resolution_days": 0}

        return {
            "count": len(resolution_times),
            "avg_resolution_days": sum(resolution_times) / len(resolution_times),
            "max_resolution_days": max(resolution_times),
            "min_resolution_days": min(resolution_times),
        }

    def get_longest_resolution_issue(self, issues: list[Issue]) -> dict[str, any]:
        """Get the issue with the longest resolution time."""
        if not issues:
            return {}

        longest_resolution_issue = None
        max_resolution_days = 0

        for issue in issues:
            try:
                # Validate issue object
                if (
                    not hasattr(issue, "fields")
                    or not hasattr(issue.fields, "created")
                    or not hasattr(issue.fields, "updated")
                ):
                    continue

                if issue.resolution_time_days > max_resolution_days:
                    max_resolution_days = issue.resolution_time_days
                    longest_resolution_issue = {
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "priority": (
                            issue.fields.priority.name
                            if issue.fields.priority
                            else "None"
                        ),
                        "resolution_days": issue.resolution_time_days,
                        "created_date": issue.fields.created,
                        "updated_date": issue.fields.updated,
                    }
            except Exception as e:
                issue_key = getattr(issue, "key", "Unknown")
                self.logger.error(
                    f"Error calculating resolution time for issue {issue_key}: {e}"
                )

        return longest_resolution_issue

    def classify_priority(self, priority_name: str) -> str:
        """Classify priority into critical, major, or minor categories."""
        if not priority_name:
            return "minor"

        priority_lower = priority_name.lower()

        # Map priorities to categories
        if priority_lower in ["highest", "high"]:
            return "critical"
        elif priority_lower == "medium":
            return "major"
        elif priority_lower in ["low", "lowest"]:
            return "minor"
        else:
            # Default to minor for unknown priorities
            return "minor"

    def calculate_priority_distribution(self, issues: list[Issue]) -> dict[str, any]:
        """Calculate priority distribution for a list of issues."""
        priority_counts = {"critical": 0, "major": 0, "minor": 0, "total": len(issues)}

        for issue in issues:
            try:
                priority_name = (
                    issue.fields.priority.name if issue.fields.priority else "None"
                )
                priority_category = self.classify_priority(priority_name)
                priority_counts[priority_category] += 1
            except Exception as e:
                self.logger.error(f"Error classifying priority: {e}")
                priority_counts["minor"] += 1  # Default to minor

        return priority_counts

    def get_sprint_detailed_metrics(self, issues: list[Issue]) -> dict[str, any]:
        """Get comprehensive metrics for a sprint
        including resolution and priority data.
        """
        if not issues:
            return {
                "total_issues": 0,
                "resolution_metrics": {},
                "longest_resolution_issue": {},
                "priority_distribution": {
                    "critical": 0,
                    "major": 0,
                    "minor": 0,
                    "total": 0,
                },
            }

        # Filter out invalid issues (those without fields attribute)
        valid_issues = []
        for issue in issues:
            if hasattr(issue, "fields") and hasattr(issue, "key"):
                valid_issues.append(issue)
            else:
                self.logger.warning(f"Skipping invalid issue object: {type(issue)}")

        if not valid_issues:
            self.logger.info("No valid issues found for metrics calculation")
            return {
                "total_issues": 0,
                "resolution_metrics": {},
                "longest_resolution_issue": {},
                "priority_distribution": {
                    "critical": 0,
                    "major": 0,
                    "minor": 0,
                    "total": 0,
                },
            }

        self.logger.debug(
            f"Processing {len(valid_issues)} valid issues out of {len(issues)} total"
        )

        return {
            "total_issues": len(valid_issues),
            "resolution_metrics": self.calculate_resolution_metrics(valid_issues),
            "longest_resolution_issue": self.get_longest_resolution_issue(valid_issues),
            "priority_distribution": self.calculate_priority_distribution(valid_issues),
        }

    def get_wip_violations_for_issues(self, issues: list[Issue]) -> dict[str, any]:
        """Get WIP limit violations from issues using changelogs for precise timing."""
        violations = {
            "total_violations": 0,
            "violations_by_status": defaultdict(lambda: {
                "count": 0,
                "issues": [],
                "longest_duration": 0,
                "total_duration": 0
            }),
            "violation_details": []
        }

        wip_labels = {
            WIPLabels.TODO_LIMIT_EXCEEDED.value: "To Do",
            WIPLabels.INPROGRESS_LIMIT_EXCEEDED.value: "In Progress",
            WIPLabels.REVIEWANDTESTING_LIMIT_EXCEEDED.value: "Review and Testing",
            WIPLabels.BLOCKED_LIMIT_EXCEEDED.value: "Blocked",
            WIPLabels.QAREVIEW_LIMIT_EXCEEDED.value: "QA Review",
        }

        for issue in issues:
            try:
                # Check if issue has WIP violation labels
                if not self._issue_has_wip_violations(issue, wip_labels):
                    continue

                # Get changelogs to calculate precise violation duration
                changelogs = self.get_issue_changelogs(issue.key)
                self.logger.debug(f"Got the changelogs for {issue.key}")
                self.logger.debug(changelogs)
                wip_violation_periods = self._calculate_wip_violation_periods(
                    changelogs, wip_labels, issue
                )
                self.logger.debug(f"Got the Violation periods for {issue.key}")
                self.logger.debug(wip_violation_periods)

                for violation in wip_violation_periods:
                    status_name = violation["status"]
                    duration_days = violation["duration_days"]

                    violations["total_violations"] += 1
                    violations["violations_by_status"][status_name]["count"] += 1

                    # Get detailed ticket information using correct model attributes
                    ticket_details = {
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "duration_days": duration_days,
                        "violation_start": violation["start_date"],
                        "violation_end": violation["end_date"],
                        "label": violation["label"],
                        # Additional ticket details for analysis
                        "priority": issue.fields.priority.name if issue.fields.priority else 'Unknown',
                        "status": issue.fields.status.name if issue.fields.status else 'Unknown',
                        "assignee": issue.fields.assignee.display_name if issue.fields.assignee else 'Unassigned',
                        "created": issue.fields.created,
                        "updated": issue.fields.updated,
                        "issue_type": issue.fields.issue_type.name if issue.fields.issue_type else 'Unknown',
                        "labels": issue.fields.labels if issue.fields.labels else []
                    }

                    violations["violations_by_status"][status_name]["issues"].append(ticket_details)
                    violations["violations_by_status"][status_name]["total_duration"] += duration_days

                    if duration_days > violations["violations_by_status"][status_name]["longest_duration"]:
                        violations["violations_by_status"][status_name]["longest_duration"] = duration_days

                    violations["violation_details"].append({
                        "issue_key": issue.key,
                        "status": status_name,
                        "duration_days": duration_days,
                        "violation_type": violation["label"],
                        "start_date": violation["start_date"],
                        "end_date": violation["end_date"]
                    })

            except Exception as e:
                self.logger.error(
                    f"Error analyzing WIP violations for issue"
                    f" {getattr(issue, 'key', 'Unknown')}: {e}"
                )

        return dict(violations)

    def get_prod_bug_analysis(self, issues: list[Issue]) -> dict[str, any]:
        """Analyze prod bug tickets by priority distribution."""
        prod_bugs = []

        for issue in issues:
            try:
                # Check if issue has prod bug label
                if self._is_prod_bug(issue):
                    prod_bugs.append(issue)
            except Exception as e:
                self.logger.error(f"Error checking prod bug for issue {getattr(issue, 'key', 'Unknown')}: {e}")

        # Calculate priority distribution for prod bugs
        priority_distribution = self.calculate_priority_distribution(prod_bugs)

        return {
            "total_prod_bugs": len(prod_bugs),
            "priority_distribution": priority_distribution,
            "prod_bug_issues": [
                {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "priority": getattr(issue.fields.priority, 'name', 'Unknown') if hasattr(issue.fields, 'priority') and issue.fields.priority else 'Unknown',
                    "priority_category": self.classify_priority(
                        getattr(issue.fields.priority, 'name', '') if hasattr(issue.fields, 'priority') and issue.fields.priority else ''
                    )
                }
                for issue in prod_bugs
            ]
        }

    def _is_prod_bug(self, issue: Issue) -> bool:
        """Check if issue has prod bug label."""
        try:
            # Check regular labels field
            if hasattr(issue.fields, 'labels') and issue.fields.labels:
                for label in issue.fields.labels:
                    if 'prod' in label.lower() and 'bug' in label.lower():
                        return True

            # Check custom fields that might contain prod bug labels
            if hasattr(issue.fields, 'customfield_10043') and issue.fields.customfield_10043:
                label_value = issue.fields.customfield_10043
                if isinstance(label_value, str) and 'prod' in label_value.lower() and 'bug' in label_value.lower():
                    return True

            return False
        except Exception as e:
            self.logger.error(f"Error checking prod bug label for issue {getattr(issue, 'key', 'Unknown')}: {e}")
            return False

    def _issue_has_wip_violations(self, issue: Issue, wip_labels: dict) -> bool:
        """Check if issue has any WIP violation labels."""
        try:
            # Check if the WIP custom field has any of the violation labels
            if issue.fields.customfield_10043:
                # Check if the value matches any of the WIP violation labels
                field_value = str(issue.fields.customfield_10043)
                return any(label in field_value for label in wip_labels.keys())

            return False
        except Exception as e:
            self.logger.error(
                f"Error checking WIP labels for issue "
                f"{getattr(issue, 'key', 'Unknown')}: {e}"
            )
            return False

    def _calculate_wip_violation_periods(
        self,
        changelogs: list[Changelog],
        wip_labels: dict,
        issue: Issue
    ) -> list[dict]:
        """Calculate precise WIP violation periods using changelogs."""
        violation_periods = []

        try:
            # Sort changelogs by date
            sorted_changelogs = sorted(changelogs, key=lambda c: isoparse(c.created))

            # Track active violations
            active_violations = {}  # {label: start_date}

            for changelog in sorted_changelogs:
                changelog_date = isoparse(changelog.created)

                # Check for changes
                for item in changelog.items:
                    # Check for WIP custom field changes (customfield_10043)
                    if (
                        item.field_id == "customfield_10043"
                        or item.field == "WIP Violation"
                    ):
                        # Handle WIP violation field changes
                        self._process_wip_field_changes(
                            item,
                            changelog_date,
                            wip_labels,
                            active_violations,
                            violation_periods
                        )

                    # Check for status changes that end violations
                    elif item.field_id == "status" or item.field == "status":
                        self._end_violations_on_status_change(
                            changelog_date,
                            active_violations,
                            violation_periods,
                            wip_labels
                        )

            # Handle any violations that are still active (no status change yet)
            current_time = isoparse(issue.fields.updated)
            for label, start_date in active_violations.items():
                if label in wip_labels:
                    duration = (current_time - start_date).days
                    violation_periods.append({
                        "label": label,
                        "status": wip_labels[label],
                        "start_date": start_date.isoformat(),
                        "end_date": current_time.isoformat(),
                        "duration_days": max(duration, 1)  # Minimum 1 day
                    })

        except Exception as e:
            self.logger.error(f"Error calculating WIP violation periods: {e}")

        return violation_periods

    def _process_wip_field_changes(
        self,
        item: ChangelogItem,
        changelog_date,
        wip_labels: dict,
        active_violations: dict,
        violation_periods: list
    ):
        """Process WIP custom field changes."""
        try:
            # Handle WIP violation field changes (custom field)
            from_value = item.from_string
            to_value = item.to_string

            # If a WIP violation was added
            if to_value and to_value in wip_labels:
                active_violations[to_value] = changelog_date
                self.logger.debug(
                    f"Started tracking WIP violation:"
                    f"{to_value} at {changelog_date}"
                )

            # If a WIP violation was removed (field cleared)
            if from_value and from_value in wip_labels and not to_value:
                if from_value in active_violations:
                    start_date = active_violations.pop(from_value)
                    duration = (changelog_date - start_date).days
                    violation_periods.append({
                        "label": from_value,
                        "status": wip_labels[from_value],
                        "start_date": start_date.isoformat(),
                        "end_date": changelog_date.isoformat(),
                        "duration_days": max(duration, 1)  # Minimum 1 day
                    })
                    self.logger.debug(
                        f"Ended WIP violation: {from_value}"
                        f"duration: {duration} days"
                    )

        except Exception as e:
            self.logger.error(f"Error processing WIP field changes: {e}")

    def _end_violations_on_status_change(
        self,
        changelog_date,
        active_violations: dict,
        violation_periods: list,
        wip_labels: dict
    ):
        """End active violations when status changes."""
        try:
            # When status changes, end all active violations
            for label, start_date in list(active_violations.items()):
                if label in wip_labels:
                    duration = (changelog_date - start_date).days
                    violation_periods.append({
                        "label": label,
                        "status": wip_labels[label],
                        "start_date": start_date.isoformat(),
                        "end_date": changelog_date.isoformat(),
                        "duration_days": max(duration, 1)  # Minimum 1 day
                    })

            # Clear all active violations after status change
            active_violations.clear()

        except Exception as e:
            self.logger.error(f"Error ending violations on status change: {e}")
