from datetime import timedelta
from core.logger import Logger
from core.enums import Status
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
        analysis_type: str = "combined",
    ) -> dict[str, any]:
        """Analyze a single project and its scrum boards.

        Args:
            analysis_type: "combined", "resolution_metrics", or "status_metrics"
        """
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
                board_result = self._analyze_board(
                    board, project, sprint_filter_config, analysis_type
                )
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
        self,
        board: any,
        project: str,
        sprint_filter_config: dict[str, any] = None,
        analysis_type: str = "combined",
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
                sprint_result = self._analyze_sprint(sprint, project, analysis_type)
                board_result["sprints"].append(sprint_result)
                board_result["total_issues"] += sprint_result["issue_count"]

        except Exception as e:
            self.logger.error(f"Error analyzing board {board.id}: {e}")

        return board_result

    def _analyze_sprint(
        self, sprint: any, project: str, analysis_type: str = "combined"
    ) -> dict[str, any]:
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

        # Get metrics based on analysis type
        result = {
            "sprint_info": sprint_info,
            "issues": bugs_details,
            "issue_count": len(bugs),
        }

        if analysis_type in ["combined", "resolution_metrics"]:
            detailed_metrics = self.issue_service.get_sprint_detailed_metrics(bugs)
            result["metrics"] = detailed_metrics

        if analysis_type in ["combined", "status_metrics"]:
            average_time_in_status = self.issue_service.get_avg_time_per_status(
                issues, sprint
            )
            max_age_per_status = self.issue_service.get_max_age_per_status(
                issues, sprint
            )
            result["status_deltas"] = average_time_in_status
            result["max_age_per_status"] = max_age_per_status

        # Include WIP limit violations and prod bug analysis for combined analysis only
        if analysis_type == "combined":
            wip_violations = self.issue_service.get_wip_violations_for_issues(issues)
            result["wip_violations"] = wip_violations

            prod_bug_analysis = self.issue_service.get_prod_bug_analysis(issues)
            result["prod_bugs"] = prod_bug_analysis

        return result

    def analyze_resolution_metrics_only(
        self,
        project: str,
        scrum_board_ids: list[int],
        sprint_filter_config: dict[str, any] = None,
    ) -> dict[str, any]:
        """Analyze project focusing only on resolution time metrics."""
        return self.analyze_project(
            project, scrum_board_ids, sprint_filter_config, "resolution_metrics"
        )

    def analyze_status_metrics_only(
        self,
        project: str,
        scrum_board_ids: list[int],
        sprint_filter_config: dict[str, any] = None,
    ) -> dict[str, any]:
        """Analyze project focusing only on status time metrics."""
        return self.analyze_project(
            project, scrum_board_ids, sprint_filter_config, "status_metrics"
        )

    def generate_resolution_report(self, results: dict[str, any]) -> str:
        """Generate report focused on resolution metrics."""
        return self.generate_report(results, "resolution_metrics")

    def generate_status_report(self, results: dict[str, any]) -> str:
        """Generate report focused on status metrics."""
        return self.generate_report(results, "status_metrics")

    def analyze_prod_bugs_only(
        self,
        project: str,
        scrum_board_ids: list[int],
        sprint_filter_config: dict[str, any] = None,
    ) -> dict[str, any]:
        """Analyze project focusing only on prod bug metrics."""
        self.logger.debug(f"Starting prod bug analysis for project: {project}")

        results = {
            "project": project,
            "boards": [],
            "total_prod_bugs": 0,
            "filter_config_used": sprint_filter_config,
        }

        try:
            # Get boards for the project
            boards = self.board_service.get_boards_for_project(project)
            scrum_boards = self.board_service.filter_scrum_boards(
                boards, scrum_board_ids
            )

            for board in scrum_boards:
                board_result = self._analyze_board_prod_bugs(
                    board, project, sprint_filter_config
                )
                results["boards"].append(board_result)
                results["total_prod_bugs"] += board_result.get(
                    "total_prod_bugs", 0
                )

        except Exception as e:
            self.logger.error(f"Error analyzing prod bugs for project {project}: {e}")

        return results

    def _analyze_board_prod_bugs(
        self, board: any, project: str, sprint_filter_config: dict[str, any] = None
    ) -> dict[str, any]:
        """Analyze prod bugs for a single board."""
        self.logger.debug(
            f"Analyzing prod bugs for board: {board.name} (ID: {board.id})"
        )

        board_result = {
            "board_info": self.board_service.get_board_info(board),
            "sprints": [],
            "total_prod_bugs": 0,
        }

        try:
            # Get sprints based on filter configuration
            sprints = self.sprint_service.get_sprints_for_board(
                board.id, sprint_filter_config
            )

            for sprint in sprints:
                # Get issues for this sprint
                issues = self.issue_service.get_bugs_for_sprint(project, sprint.id)
                sprint_prod_bugs = self.issue_service.get_prod_bug_analysis(issues)

                sprint_info = self.sprint_service.get_sprint_info(sprint)
                sprint_result = {
                    "sprint_info": sprint_info,
                    "prod_bugs": sprint_prod_bugs,
                }

                board_result["sprints"].append(sprint_result)
                board_result["total_prod_bugs"] += sprint_prod_bugs.get(
                    "total_prod_bugs", 0
                )

        except Exception as e:
            self.logger.error(f"Error analyzing prod bugs for board {board.id}: {e}")

        return board_result

    def generate_prod_bugs_report(self, results: dict[str, any]) -> str:
        """Generate report focused on prod bug analysis."""
        report = []
        report.append(
            f"\n=== Prod Bug Analysis Report for Project: {results['project']} ==="
        )
        report.append(f"Total Prod Bugs: {results.get('total_prod_bugs', 0)}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        if not results.get("boards"):
            report.append(f"\nNo boards found for project {results['project']}")
            return "\n".join(report)

        report.append("\n=== Board Details ===")
        for board_result in results["boards"]:
            board_info = board_result["board_info"]
            report.append(f"\nBoard: {board_info['name']} (ID: {board_info['id']})")
            report.append(f"Total Prod Bugs: {board_result.get('total_prod_bugs', 0)}")

            for sprint_result in board_result["sprints"]:
                sprint_info = sprint_result["sprint_info"]
                prod_bugs = sprint_result.get("prod_bugs", {})

                if prod_bugs.get("total_prod_bugs", 0) > 0:
                    priority_dist = prod_bugs["priority_distribution"]
                    report.append(
                        f"\n  Sprint: {sprint_info['name']} - "
                        f"{prod_bugs['total_prod_bugs']} prod bugs"
                    )
                    report.append(
                        f"\n  Start: {sprint_info['start_date']} - "
                        f"Complete: {sprint_info['complete_date']}"
                    )
                    report.append(f"    Critical: {priority_dist['critical']}")
                    report.append(f"    Major: {priority_dist['major']}")
                    report.append(f"    Minor: {priority_dist['minor']}")

                    # Show individual prod bugs
                    if prod_bugs.get("prod_bug_issues"):
                        report.append("    Issues:")
                        for bug in prod_bugs["prod_bug_issues"][:5]:  # Show first 5
                            report.append(
                                f"      {bug['key']} ({bug['priority']}): "
                                f"{bug['summary'][:50]}..."
                            )
                else:
                    report.append(f"\n  Sprint: {sprint_info['name']} - No prod bugs")

        return "\n".join(report)

    def generate_prod_bugs_quarterly_report(self, results: dict[str, any]) -> str:
        """Generate quarterly prod bug report grouped by quarters."""
        from datetime import datetime
        from collections import defaultdict

        report = []
        report.append(
            f"\n=== Quarterly Prod Bug Analysis Report for Project: {results['project']} ==="
        )
        report.append(f"Total Prod Bugs: {results.get('total_prod_bugs', 0)}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        if not results.get("boards"):
            report.append(f"\nNo boards found for project {results['project']}")
            return "\n".join(report)

        # Group sprints by quarter
        quarterly_data = defaultdict(lambda: {
            "total_prod_bugs": 0,
            "priority_distribution": {"critical": 0, "major": 0, "minor": 0},
            "sprints": []
        })

        for board_result in results["boards"]:
            for sprint_result in board_result["sprints"]:
                sprint_info = sprint_result["sprint_info"]
                prod_bugs = sprint_result.get("prod_bugs", {})

                if not sprint_info.get("start_date"):
                    continue

                try:
                    # Parse sprint start date and determine quarter
                    start_date = datetime.fromisoformat(
                        sprint_info["start_date"].replace("Z", "+00:00")
                    )
                    year = start_date.year
                    quarter = (start_date.month - 1) // 3 + 1
                    quarter_key = f"Q{quarter} {year}"

                    # Add data to quarterly summary
                    quarterly_data[quarter_key]["total_prod_bugs"] += prod_bugs.get(
                        "total_prod_bugs", 0
                    )

                    if prod_bugs.get("priority_distribution"):
                        priority_dist = prod_bugs["priority_distribution"]
                        q_priority = quarterly_data[quarter_key]["priority_distribution"]
                        q_priority["critical"] += priority_dist.get("critical", 0)
                        q_priority["major"] += priority_dist.get("major", 0)
                        q_priority["minor"] += priority_dist.get("minor", 0)

                    quarterly_data[quarter_key]["sprints"].append({
                        "sprint_name": sprint_info["name"],
                        "prod_bugs": prod_bugs.get("total_prod_bugs", 0),
                        "priority_dist": prod_bugs.get("priority_distribution", {})
                    })

                except Exception as e:
                    self.logger.error(f"Error parsing sprint date: {e}")
                    continue

        # Sort quarters chronologically
        sorted_quarters = sorted(
            quarterly_data.keys(),
            key=lambda x: (int(x.split()[-1]), int(x.split()[0][1:]))
        )

        report.append("\n=== Quarterly Summary ===")
        for quarter in sorted_quarters:
            data = quarterly_data[quarter]
            report.append(f"\n{quarter}:")
            report.append(f"  Total Prod Bugs: {data['total_prod_bugs']}")

            if data["total_prod_bugs"] > 0:
                priority_dist = data["priority_distribution"]
                report.append(f"  Critical: {priority_dist['critical']}")
                report.append(f"  Major: {priority_dist['major']}")
                report.append(f"  Minor: {priority_dist['minor']}")

                # Show sprint breakdown
                report.append("  Sprints:")
                for sprint in data["sprints"]:
                    if sprint["prod_bugs"] > 0:
                        report.append(
                            f"    {sprint['sprint_name']}: "
                            f"{sprint['prod_bugs']} prod bugs"
                        )

        return "\n".join(report)

    def analyze_wip_violations_only(
        self,
        project: str,
        scrum_board_ids: list[int],
        sprint_filter_config: dict[str, any] = None,
    ) -> dict[str, any]:
        """Analyze project focusing only on WIP limit violations."""
        self.logger.debug(f"Starting WIP violations analysis for project: {project}")

        results = {
            "project": project,
            "boards": [],
            "total_violations": 0,
            "filter_config_used": sprint_filter_config,
        }

        try:
            # Get boards for the project
            boards = self.board_service.get_boards_for_project(project)
            scrum_boards = self.board_service.filter_scrum_boards(
                boards, scrum_board_ids
            )

            for board in scrum_boards:
                board_result = self._analyze_board_wip_violations(
                    board, project, sprint_filter_config
                )
                results["boards"].append(board_result)
                results["total_violations"] += board_result.get("total_violations", 0)

        except Exception as e:
            self.logger.error(
                f"Error analyzing WIP violations for project {project}: {e}"
            )

        return results

    def _analyze_board_wip_violations(
        self, board: any, project: str, sprint_filter_config: dict[str, any] = None
    ) -> dict[str, any]:
        """Analyze WIP violations for a single board."""
        self.logger.debug(
            f"Analyzing WIP violations for board: {board.name} (ID: {board.id})"
        )

        board_result = {
            "board_info": self.board_service.get_board_info(board),
            "sprints": [],
            "total_violations": 0,
        }

        try:
            # Get sprints based on filter configuration
            sprints = self.sprint_service.get_sprints_for_board(
                board.id, sprint_filter_config
            )

            for sprint in sprints:
                # Get issues for this sprint (reuse from main flow)
                issues = self.issue_service.get_issues_for_sprint(project, sprint.id)

                sprint_wip_violations = (
                    self.issue_service.get_wip_violations_for_issues(issues)
                )
                sprint_prod_bugs = self.issue_service.get_prod_bug_analysis(issues)

                sprint_info = self.sprint_service.get_sprint_info(sprint)
                sprint_result = {
                    "sprint_info": sprint_info,
                    "wip_violations": sprint_wip_violations,
                    "prod_bugs": sprint_prod_bugs,
                }

                board_result["sprints"].append(sprint_result)
                board_result["total_violations"] += sprint_wip_violations.get(
                    "total_violations", 0
                )

        except Exception as e:
            self.logger.error(
                f"Error analyzing WIP violations for board {board.id}: {e}"
            )

        return board_result

    def generate_wip_violations_report(self, results: dict[str, any]) -> str:
        """Generate report focused on WIP limit violations."""
        report = []
        report.append(
            f"\n=== WIP Limit Violations Report for Project: {results['project']} ==="
        )
        report.append(f"Total Violations: {results.get('total_violations', 0)}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        if not results.get("boards"):
            report.append(f"\nNo boards found for project {results['project']}")
            return "\n".join(report)

        report.append("\n=== Board Details ===")
        for board_result in results["boards"]:
            board_info = board_result["board_info"]
            report.append(f"\nBoard: {board_info['name']} (ID: {board_info['id']})")
            report.append(
                f"Total Violations: {board_result.get('total_violations', 0)}"
            )

            for sprint_result in board_result["sprints"]:
                sprint_info = sprint_result["sprint_info"]
                wip_violations = sprint_result.get("wip_violations", {})
                report.append(
                    f"\n  Start: {sprint_info['start_date']} - "
                    f"Complete: {sprint_info['complete_date']}"
                )
                if wip_violations.get("total_violations", 0) > 0:
                    wip_report = self._format_wip_violations_report(
                        wip_violations, sprint_info["name"]
                    )
                    report.append(f"\n  {wip_report}")
                else:
                    report.append(
                        f"\n  Sprint: {sprint_info['name']} - No WIP violations"
                    )

            # Add violation categorization by actual duration from changelogs
            report.append(self._generate_violation_categorization(board_result))

        return "\n".join(report)

    def _generate_violation_categorization(self, board_result: dict[str, any]) -> str:
        """Generate categorization of violations by duration from changelog analysis."""
        categorization = []
        categorization.append("\n=== Violation Duration Analysis ===")

        # Collect all violations with their actual durations from changelogs
        all_violations = []
        for sprint_result in board_result["sprints"]:
            wip_violations = sprint_result.get("wip_violations", {})
            violations_by_status = wip_violations.get("violations_by_status", {})

            for status, status_data in violations_by_status.items():
                issues = status_data.get("issues", [])
                for issue in issues:
                    all_violations.append({
                        "key": issue["key"],
                        "summary": issue["summary"],
                        "duration_days": issue["duration_days"],
                        "status": status,
                        "sprint": sprint_result["sprint_info"]["name"]
                    })

        if not all_violations:
            categorization.append("No violations found")
            return "\n".join(categorization)

        # Sort violations by duration (longest first)
        all_violations.sort(key=lambda x: x["duration_days"], reverse=True)

        # Show all violations with their actual durations
        categorization.append(f"\nTotal Violations: {len(all_violations)}")
        categorization.append("\nViolations by Duration (Longest to Shortest):")

        for violation in all_violations:
            categorization.append(
                f"  {violation['key']}: {violation['duration_days']} days in {violation['status']} "
                f"- {violation['summary'][:60]}..."
            )

        return "\n".join(categorization)

    def generate_report(
        self, results: dict[str, any], report_type: str = "combined"
    ) -> str:
        """Generate a formatted report from analysis results.

        Args:
            report_type: "combined", "resolution_metrics", or "status_metrics"
        """
        if report_type == "resolution_metrics":
            return self._generate_resolution_report(results)
        elif report_type == "status_metrics":
            return self._generate_status_report(results)
        else:
            return self._generate_combined_report(results)

    def _generate_combined_report(self, results: dict[str, any]) -> str:
        """Generate combined report with both resolution and status metrics."""
        report = []
        report.append(
            f"\n=== Combined Jira Analysis Report for Project: {results['project']} ==="
        )
        report.append(f"Total Issues Analyzed: {results['total_issues']}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        # Add overall resolution metrics
        if results.get("total_resolution_metrics", {}).get("count", 0) > 0:
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
                self._add_sprint_to_report(report, sprint_result)

        return "\n".join(report)

    def _generate_resolution_report(self, results: dict[str, any]) -> str:
        """Generate report focused on resolution time metrics."""
        report = []
        report.append(
            f"\n=== Resolution Time Analysis Report for Project:"
            f"{results['project']} ==="
        )
        report.append(f"Total Issues Analyzed: {results['total_issues']}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        # Add overall resolution metrics
        if results.get("total_resolution_metrics", {}).get("count", 0) > 0:
            metrics = results["total_resolution_metrics"]
            report.append("\n=== Overall Resolution Metrics ===")
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
                self._add_sprint_to_report(report, sprint_result, resolution_only=True)

        return "\n".join(report)

    def _generate_status_report(self, results: dict[str, any]) -> str:
        """Generate report focused on status time metrics."""
        report = []
        report.append(
            f"\n=== Status Time Analysis Report for Project: {results['project']} ==="
        )
        report.append(f"Total Issues Analyzed: {results['total_issues']}")

        # Add filter configuration info
        self._add_filter_config_to_report(report, results)

        if not results.get("boards"):
            report.append(f"\nNo Scrum boards found for project {results['project']}")
            return "\n".join(report)

        report.append("\n=== Board Details ===")
        for board_result in results["boards"]:
            board_info = board_result["board_info"]
            report.append(f"\nBoard: {board_info['name']} (ID: {board_info['id']})")
            report.append(f"Total Issues: {board_result['total_issues']}")

            for sprint_result in board_result["sprints"]:
                self._add_sprint_to_report(report, sprint_result, status_only=True)

        return "\n".join(report)

    def _add_filter_config_to_report(
        self, report: list[str], results: dict[str, any]
    ) -> None:
        """Add filter configuration info to report."""
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

    def _add_sprint_to_report(
        self,
        report: list[str],
        sprint_result: dict[str, any],
        resolution_only: bool = False,
        status_only: bool = False,
    ) -> None:
        """Add sprint information to report based on type."""
        sprint_info = sprint_result["sprint_info"]
        report.append(
            f"\n  Sprint: {sprint_info['name']} ({sprint_info['state']}) - "
            f"{sprint_result['issue_count']} issues"
        )

        if not sprint_result.get("issue_count"):
            report.append(f"    No issues found for sprint {sprint_info['name']}\n")
            return

        # Add resolution metrics if available and requested
        if not status_only and sprint_result.get("metrics"):
            metrics = sprint_result["metrics"]

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
                report.append(f"      Max: {res_metrics['max_resolution_days']} days")
                report.append(f"      Min: {res_metrics['min_resolution_days']} days")

        # Add status timedeltas if available and requested
        if sprint_result.get("status_deltas"):
            status_deltas: dict[str, timedelta] = sprint_result["status_deltas"]
            if status_deltas:  # Only show if there are actually status deltas
                report.append("    Average Status Time Breakdown:")
                for status_id, delta in status_deltas.items():
                    status_name = Status.get_status_name(status_id)
                    report.append(f"      {status_name}: {delta.days} days (avg)")

        # Add max age per status if available (status reports only)
        if status_only and sprint_result.get("max_age_per_status"):
            max_age_per_status = sprint_result["max_age_per_status"]
            if max_age_per_status:
                report.append("    Max Age per Status (Longest Duration Issues):")
                for status_id, data in max_age_per_status.items():
                    status_name = Status.get_status_name(status_id)
                    report.append(f"      {status_name}: {data['issue_key']} - {data['duration_days']} days")
                    report.append(f"        Summary: {data['issue_summary'][:60]}...")

        # Add WIP violations if available (non-status reports only)
        if not status_only and sprint_result.get("wip_violations"):
            wip_violations = sprint_result["wip_violations"]
            if wip_violations.get("total_violations", 0) > 0:
                wip_summary = self._get_wip_violation_summary(wip_violations)
                report.append("    WIP Limit Violations:")
                report.append(
                    f"      Total Violations: {wip_summary['total_violations']}"
                )
                report.append(
                    f"      Average Duration: "
                    f"{wip_summary['average_violation_duration']:.1f} days"
                )

                for status, data in wip_summary["status_breakdown"].items():
                    report.append(
                        f"      {status}: {data['violation_count']} "
                        f"violations (avg {data['average_duration']:.1f} days)"
                    )

        # Add prod bugs if available (non-status reports only)
        if not status_only and sprint_result.get("prod_bugs"):
            prod_bugs = sprint_result["prod_bugs"]
            if prod_bugs.get("total_prod_bugs", 0) > 0:
                priority_dist = prod_bugs["priority_distribution"]
                report.append("    Prod Bug Analysis:")
                report.append(f"      Total Prod Bugs: {prod_bugs['total_prod_bugs']}")
                report.append(f"      Critical: {priority_dist['critical']}")
                report.append(f"      Major: {priority_dist['major']}")
                report.append(f"      Minor: {priority_dist['minor']}")

    def _get_wip_violation_summary(self, violations: dict[str, any]) -> dict[str, any]:
        """Generate summary statistics for WIP violations."""
        summary = {
            "total_violations": violations.get("total_violations", 0),
            "status_breakdown": {},
            "average_violation_duration": 0,
            "longest_violation": {"status": None, "duration": 0, "issue_key": None},
        }

        violations_by_status = violations.get("violations_by_status", {})
        total_duration = 0

        for status, data in violations_by_status.items():
            count = data["count"]
            total_status_duration = data["total_duration"]
            longest_duration = data["longest_duration"]

            summary["status_breakdown"][status] = {
                "violation_count": count,
                "average_duration": total_status_duration / count if count > 0 else 0,
                "longest_duration": longest_duration,
            }

            total_duration += total_status_duration

            # Track overall longest violation
            if longest_duration > summary["longest_violation"]["duration"]:
                longest_issue = None
                for issue_data in data["issues"]:
                    if issue_data["duration_days"] == longest_duration:
                        longest_issue = issue_data["key"]
                        break

                summary["longest_violation"] = {
                    "status": status,
                    "duration": longest_duration,
                    "issue_key": longest_issue,
                }

        # Calculate overall average
        if summary["total_violations"] > 0:
            summary["average_violation_duration"] = (
                total_duration / summary["total_violations"]
            )

        return summary

    def _format_wip_violations_report(
        self, violations: dict[str, any], sprint_name: str = None
    ) -> str:
        """Format WIP violations into a readable report."""
        if not violations or violations.get("total_violations", 0) == 0:
            return (
                f"No WIP limit violations found"
                f"{' for sprint ' + sprint_name if sprint_name else ''}."
            )

        summary = self._get_wip_violation_summary(violations)
        report = []

        header = "WIP Limit Violations Report"
        if sprint_name:
            header += f" - {sprint_name}"
        report.append(f"\n=== {header} ===")

        report.append(f"Total Violations: {summary['total_violations']}")
        report.append(
            f"Average Violation Duration:"
            f" {summary['average_violation_duration']:.1f} days"
        )

        if summary["longest_violation"]["status"]:
            report.append(
                f"Longest Violation: "
                f"{summary['longest_violation']['duration']} days in "
                f"{summary['longest_violation']['status']} "
                f"({summary['longest_violation']['issue_key']})"
            )

        report.append("\n=== Violations by Status ===")

        for status, data in summary["status_breakdown"].items():
            report.append(f"\n{status}:")
            report.append(f"  Violation Count: {data['violation_count']}")
            report.append(f"  Average Duration: {data['average_duration']:.1f} days")
            report.append(f"  Longest Duration: {data['longest_duration']} days")

            # Show individual violations for this status
            status_violations = violations["violations_by_status"][status]["issues"]
            if status_violations:
                report.append("  Issues:")
                for issue in status_violations[:5]:  # Show first 5
                    report.append(
                        f"    {issue['key']}: {issue['duration_days']} days"
                        f" - {issue['summary'][:50]}..."
                    )

        return "\n".join(report)
