from datetime import timedelta
from dateutil.parser import isoparse
from collections import defaultdict

from core.logger import Logger
from core.enums import WIPLabels
from services.jira.models import Issue
from services.jira.models.sprint import Sprint
from services.jira.models.tracking import Changelog, ChangelogItem


class IssueService:
    """Service class for handling issue-related operations."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()

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
                from_status = status_item.from_id or status_item.from_string
                if from_status is None:
                    continue
                groups[from_status].append(cl)
        except Exception as e:
            self.logger.error(f"Error while grouping changelogs by status {e}")
        return dict(groups)

    def calculate_time_per_status(
        self, status_changelogs: list[Changelog]
    ) -> dict[str, timedelta]:
        """Calculate the time in status"""
        status_deltas: dict[str, timedelta] = defaultdict(timedelta)
        try:
            sorted_changelogs = sorted(
                status_changelogs, key=lambda c: isoparse(c.created)
            )
            for c in range(len(sorted_changelogs) - 2):
                status_item: ChangelogItem = next(
                    (
                        it
                        for it in sorted_changelogs[c].items
                        if it.field_id == "status"
                    ),
                    None,
                )
                from_status: str = status_item.from_id or status_item.from_string

                status_deltas[from_status] += isoparse(
                    sorted_changelogs[c + 1].created
                ) - isoparse(sorted_changelogs[c].created)
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
                issue_status_times = self.calculate_time_per_status(status_changelogs)

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
                    violations["violations_by_status"][status_name]["issues"].append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "duration_days": duration_days,
                        "violation_start": violation["start_date"],
                        "violation_end": violation["end_date"],
                        "label": violation["label"]
                    })
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

    def _issue_has_wip_violations(self, issue: Issue, wip_labels: dict) -> bool:
        """Check if issue has any WIP violation labels."""
        try:
            # Check if the WIP custom field has any of the violation labels
            if issue.fields.customfield_10043:
                return True

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
