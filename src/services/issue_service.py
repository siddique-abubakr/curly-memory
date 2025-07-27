from datetime import datetime
from typing import List, Dict, Any
from core.logger import Logger


class IssueService:
    """Service class for handling issue-related operations."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger(name=__name__)

    def get_done_bugs_for_sprint(self, project: str, sprint_id: int) -> List[Any]:
        """Get all done bugs for a specific sprint."""
        try:
            jql = (
                f"project = {project} AND "
                f"sprint = {sprint_id} AND "
                f"type = Bug AND status = Done"
            )
            issues = self.jira.search_issues(jql)
            self.logger.debug(f"Found {len(issues)} done bugs for sprint {sprint_id}")
            return issues
        except Exception as e:
            self.logger.error(f"Error fetching issues for sprint {sprint_id}: {e}")
            return []

    def get_issue_info(self, issue) -> Dict[str, Any]:
        """Get formatted issue information."""
        try:
            created_date = datetime.fromisoformat(issue.fields.created)
            updated_date = datetime.fromisoformat(issue.fields.updated)
            resolution_time = updated_date - created_date

            return {
                "id": issue.id,
                "key": issue.key,
                "summary": issue.fields.summary,
                "priority": (
                    issue.fields.priority.name if issue.fields.priority else "None"
                ),
                "created_date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_date": updated_date.strftime("%Y-%m-%d %H:%M:%S"),
                "resolution_time_days": resolution_time.days,
                "resolution_time": str(resolution_time),
            }
        except Exception as e:
            self.logger.error(f"Error getting issue info: {e}")
            return {}

    def calculate_resolution_metrics(self, issues: List[Any]) -> Dict[str, Any]:
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

                created_date = datetime.fromisoformat(issue.fields.created)
                updated_date = datetime.fromisoformat(issue.fields.updated)
                resolution_time = (updated_date - created_date).days
                resolution_times.append(resolution_time)
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

    def get_longest_resolution_issue(self, issues: List[Any]) -> Dict[str, Any]:
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

                created_date = datetime.fromisoformat(issue.fields.created)
                updated_date = datetime.fromisoformat(issue.fields.updated)
                resolution_time = (updated_date - created_date).days

                if resolution_time > max_resolution_days:
                    max_resolution_days = resolution_time
                    longest_resolution_issue = {
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "priority": (
                            issue.fields.priority.name
                            if issue.fields.priority
                            else "None"
                        ),
                        "resolution_days": resolution_time,
                        "created_date": created_date.strftime("%Y-%m-%d"),
                        "updated_date": updated_date.strftime("%Y-%m-%d"),
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

    def calculate_priority_distribution(self, issues: List[Any]) -> Dict[str, Any]:
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

    def get_sprint_detailed_metrics(self, issues: List[Any]) -> Dict[str, Any]:
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
