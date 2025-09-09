from datetime import timedelta
from core.logger import Logger
from .board_service import BoardService
from .sprint_service import SprintService
from .issue_service import IssueService


class JiraAnalyzer:
    """Main orchestrator class for Jira analysis."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()

        # Initialize services
        self.board_service = BoardService(jira_client)
        self.sprint_service = SprintService(jira_client)
        self.issue_service = IssueService(jira_client)

    def analyze_project(
        self,
        project: str,
        scrum_board_ids: list[int],
        sprint_filter_config: dict[str, any] = None,
    ) -> dict[str, any]:
        """Analyze a single project and its scrum boards."""
        self.logger.debug(f"Starting analysis for project: {project}")

        results = {
            "project": project,
            "boards": [],
            "total_issues": 0,
            "total_resolution_metrics": {},
            "filter_config_used": sprint_filter_config,
        }

        try:
            # Get boards for the project
            boards = self.board_service.get_boards_for_project(project)
            scrum_boards = self.board_service.filter_scrum_boards(
                boards, scrum_board_ids
            )

            for board in scrum_boards:
                board_result = self._analyze_board(board, project, sprint_filter_config)
                results["boards"].append(board_result)
                results["total_issues"] += board_result["total_issues"]

            # Calculate overall metrics
            all_issues = []
            for board_result in results["boards"]:
                for sprint_result in board_result["sprints"]:
                    all_issues.extend(sprint_result["issues"])

            results["total_resolution_metrics"] = (
                self.issue_service.calculate_resolution_metrics(all_issues)
            )

        except Exception as e:
            self.logger.error(f"Error analyzing project {project}: {e}")

        return results

    def _analyze_board(
        self, board: any, project: str, sprint_filter_config: dict[str, any] = None
    ) -> dict[str, any]:
        """Analyze a single board."""
        self.logger.debug(f"Analyzing board: {board.name} (ID: {board.id})")

        board_result = {
            "board_info": self.board_service.get_board_info(board),
            "sprints": [],
            "total_issues": 0,
        }

        try:
            # Get sprints based on filter configuration
            sprints = self.sprint_service.get_sprints_for_board(
                board.id, sprint_filter_config
            )

            for sprint in sprints:
                sprint_result = self._analyze_sprint(sprint, project)
                board_result["sprints"].append(sprint_result)
                board_result["total_issues"] += sprint_result["issue_count"]

        except Exception as e:
            self.logger.error(f"Error analyzing board {board.id}: {e}")

        return board_result

    def _analyze_sprint(self, sprint: any, project: str) -> dict[str, any]:
        """Analyze a single sprint."""
        self.logger.debug(f"Analyzing sprint: {sprint.name} (ID: {sprint.id})")

        sprint_info = self.sprint_service.get_sprint_info(sprint)

        # Get done bugs for this sprint
        bugs = self.issue_service.get_done_bugs_for_sprint(project, sprint.id)
        issues = self.issue_service.get_issues_for_sprint(project, sprint.id)

        # Get detailed issue information for display
        bugs_details = []
        for issue in bugs:
            issue_info = self.issue_service.get_issue_info(issue)
            bugs_details.append(issue_info)

        # Get comprehensive metrics using raw issue objects
        detailed_metrics = self.issue_service.get_sprint_detailed_metrics(bugs)
        average_time_in_status = self.issue_service.get_avg_time_per_status(
            issues, sprint
        )

        return {
            "sprint_info": sprint_info,
            "issues": bugs_details,
            "issue_count": len(bugs),
            "metrics": detailed_metrics,
            "status_deltas": average_time_in_status,
        }

    def generate_report(self, results: dict[str, any]) -> str:
        """Generate a formatted report from analysis results."""
        report = []
        report.append(
            f"\n=== Jira Analysis Report for Project" f": {results['project']} ==="
        )
        report.append(f"Total Issues Analyzed: {results['total_issues']}")

        # Add filter configuration info
        if results.get("filter_config_used"):
            filter_config = results["filter_config_used"]
            report.append("Filter Configuration:")
            if filter_config.get("date_range", {}).get("enabled"):
                date_range = filter_config["date_range"]
                start_str = date_range["start_date"].strftime("%Y-%m-%d")
                end_str = date_range["end_date"].strftime("%Y-%m-%d")
                report.append(f"  Date Range: {start_str} to {end_str}")
            if filter_config.get("sprint_states"):
                report.append(
                    f"  Sprint States: {', '.join(filter_config['sprint_states'])}"
                )
            if filter_config.get("specific_sprint_ids"):
                report.append(
                    f"  Specific Sprint IDs: {filter_config['specific_sprint_ids']}"
                )

        if results["total_resolution_metrics"]["count"] > 0:
            metrics = results["total_resolution_metrics"]
            report.append(
                f"Average Resolution Time: {metrics['avg_resolution_days']:.1f} days"
            )
            report.append(f"Max Resolution Time: {metrics['max_resolution_days']} days")
            report.append(f"Min Resolution Time: {metrics['min_resolution_days']} days")

        if not results.get("boards"):
            report.append(f"\nNo Scrum boards found for project {results['project']}")
            return "\n".join(report)

        report.append("\n=== Board Details ===")
        for board_result in results["boards"]:
            board_info = board_result["board_info"]
            report.append(f"\nBoard: {board_info['name']} (ID: {board_info['id']})")
            report.append(f"Total Issues: {board_result['total_issues']}")

            for sprint_result in board_result["sprints"]:
                sprint_info = sprint_result["sprint_info"]
                status_deltas: dict[str, timedelta] = sprint_result["status_deltas"]
                metrics = sprint_result["metrics"]

                report.append(
                    f"\n  Sprint: {sprint_info['name']} ({sprint_info['state']}) - "
                    f"{sprint_result['issue_count']} issues"
                )

                if not sprint_result.get("issue_count"):
                    report.append(
                        f"    No issues found for sprint {sprint_info['name']}\n"
                    )

                # Add priority distribution
                if metrics.get("priority_distribution", {}).get("total", 0) > 0:
                    priority_dist = metrics["priority_distribution"]
                    report.append("    Priority Distribution:")
                    report.append(f"      Critical: {priority_dist['critical']}")
                    report.append(f"      Major: {priority_dist['major']}")
                    report.append(f"      Minor: {priority_dist['minor']}")

                # Add longest resolution time
                if metrics.get("longest_resolution_issue"):
                    longest_issue = metrics["longest_resolution_issue"]
                    report.append(
                        f"    Longest Resolution: {longest_issue['key']} - "
                        f"{longest_issue['resolution_days']} days"
                    )
                    report.append(f"      Summary: {longest_issue['summary']}")
                    report.append(f"      Priority: {longest_issue['priority']}")

                # Add resolution metrics if available
                if metrics.get("resolution_metrics", {}).get("count", 0) > 0:
                    res_metrics = metrics["resolution_metrics"]
                    report.append("    Resolution Metrics:")
                    report.append(
                        f"      Average: {res_metrics['avg_resolution_days']:.1f} days"
                    )
                    report.append(
                        f"      Max: {res_metrics['max_resolution_days']} days"
                    )
                    report.append(
                        f"      Min: {res_metrics['min_resolution_days']} days"
                    )

                # Add status timedeltas if available
                if status_deltas:
                    report.append("    Status Deltas:")
                    for k, v in status_deltas.items():
                        report.append(f"      {k}: {v.days} days")

        return "\n".join(report)
