from collections import defaultdict
from typing import Any

from core.logger import Logger
from .pr_service import PRService


class GitHubAnalyzer:
    """Main orchestrator class for GitHub analysis."""

    def __init__(self, github_client):
        self.github = github_client
        self.logger = Logger.get_logger()

        # Initialize services
        self.pr_service = PRService(github_client)

    def analyze_repository_prs(
        self,
        config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Analyze GitHub repository pull requests with comprehensive metrics.

        Args:
            config: Configuration dict containing:
                - owner: GitHub owner/organization
                - repos: List of repository names to analyze
                - grouping: "monthly" or "semi-monthly"
                - start_date: "YYYY-MM-DD" format
                - end_date: "YYYY-MM-DD" format
                - target_branch: default "develop"
        """
        if config is None:
            config = {}

        owner = config.get("owner", self.github.owner)
        repos = config.get("repos", [self.github.repo])
        grouping = config.get("grouping", "monthly")
        start_date = config.get("start_date")
        end_date = config.get("end_date")
        target_branch = config.get("target_branch", "develop")
        max_prs_per_repo = config.get("max_prs_per_repo", None)

        # Convert single repo to list for backward compatibility
        if isinstance(repos, str):
            repos = [repos]

        self.logger.info(f"Starting GitHub PR analysis for {len(repos)} repositories")
        self.logger.info(f"Repositories: {repos}")
        self.logger.info(f"Config: {config}")

        # Aggregate results across all repositories
        aggregated_results = {
            "repositories": repos,
            "owner": owner,
            "config_used": config,
            "total_prs": 0,
            "prs_with_reviews": 0,
            "periods": [],
            "overall_metrics": {},
            "repository_breakdown": [],
        }

        try:
            all_aggregated_prs = []

            # Analyze each repository
            for repo in repos:
                self.logger.info(f"Analyzing repository: {owner}/{repo}")

                try:
                    # Get all PRs with pagination for this specific repo
                    repo_prs = self._get_prs_for_repository(repo, target_branch)

                    self.logger.info(f"Repository {repo}: fetched {len(repo_prs)} total PRs")

                    # Apply filters in order of precedence:
                    # 1. Date filtering (primary filter - business logic)
                    if start_date or end_date:
                        original_count = len(repo_prs)
                        repo_prs = self.pr_service.filter_prs_by_date_range(
                            repo_prs, start_date, end_date
                        )
                        self.logger.info(f"Repository {repo}: date filter applied, {len(repo_prs)} PRs remain (filtered out {original_count - len(repo_prs)})")

                    # 2. Count limiting (performance optimization - applied after date filter)
                    if max_prs_per_repo and len(repo_prs) > max_prs_per_repo:
                        self.logger.info(f"Repository {repo}: performance limit applied, analyzing most recent {max_prs_per_repo} of {len(repo_prs)} PRs")
                        repo_prs = repo_prs[:max_prs_per_repo]

                    self.logger.info(f"Repository {repo}: final analysis set = {len(repo_prs)} PRs")

                    # Store repository-specific results
                    repo_metrics = self._analyze_prs_for_repository(repo_prs, repo)
                    repo_result = {
                        "repository": f"{owner}/{repo}",
                        "total_prs": len(repo_prs),
                        "prs_with_reviews": repo_metrics.get("prs_with_reviews", 0),
                        "metrics": repo_metrics
                    }
                    aggregated_results["repository_breakdown"].append(repo_result)

                    # Add to aggregated data
                    all_aggregated_prs.extend(repo_prs)
                    aggregated_results["total_prs"] += len(repo_prs)
                    aggregated_results["prs_with_reviews"] += repo_metrics.get("prs_with_reviews", 0)

                    self.logger.info(f"Repository {repo}: {len(repo_prs)} PRs, {repo_metrics.get('prs_with_reviews', 0)} with reviews")

                except Exception as e:
                    self.logger.error(f"Error analyzing repository {repo}: {e}")
                    # Continue with other repositories
                    continue

            if not all_aggregated_prs:
                self.logger.warning("No PRs found across all repositories matching criteria")
                return aggregated_results

            # Aggregate metrics from repository-specific analyses instead of re-analyzing
            aggregated_results["periods"] = self._aggregate_period_metrics_from_repos(
                aggregated_results["repository_breakdown"], grouping
            )

            # Calculate overall aggregated metrics from repository breakdowns
            aggregated_results["overall_metrics"] = self._aggregate_overall_metrics_from_repos(
                aggregated_results["repository_breakdown"]
            )

            # Sort periods chronologically
            aggregated_results["periods"].sort(key=lambda x: x["period_key"])

        except Exception as e:
            self.logger.error(f"Error analyzing GitHub PRs: {e}")

        return aggregated_results

    def generate_github_report(self, results: dict[str, Any]) -> str:
        """Generate a formatted report from GitHub analysis results."""
        report = []
        report.append(f"\n=== GitHub PR Analysis Report ===")

        # Handle both single and multi-repository results
        if "repositories" in results:
            report.append(f"Owner: {results['owner']}")
            report.append(f"Repositories: {', '.join(results['repositories'])}")
        else:
            # Backward compatibility
            report.append(f"Repository: {results.get('repository', 'Unknown')}")

        # Add configuration info
        self._add_config_to_report(report, results)

        report.append(f"Total PRs Analyzed: {results['total_prs']}")
        report.append(f"PRs with Reviews: {results['prs_with_reviews']}")

        # Show which filters were applied
        config = results.get("config_used", {})
        if config.get("max_prs_per_repo"):
            report.append(f"Performance Limit: Analyzing max {config['max_prs_per_repo']} PRs per repository")

        # Repository breakdown (for multi-repo analysis)
        if results.get("repository_breakdown"):
            report.append(f"\n=== Repository Breakdown ===")
            for repo_result in results["repository_breakdown"]:
                report.append(f"\n{repo_result['repository']}:")
                report.append(f"  Total PRs: {repo_result['total_prs']}")
                report.append(f"  PRs with Reviews: {repo_result['prs_with_reviews']}")

                repo_metrics = repo_result.get("metrics", {})
                if repo_metrics.get("review_time_stats"):
                    stats = repo_metrics["review_time_stats"]
                    report.append(f"  Average Review Time: {stats['mean']:.2f} hours")
                if repo_metrics.get("comment_stats"):
                    stats = repo_metrics["comment_stats"]
                    report.append(f"  Average Comments: {stats['mean']:.2f}")
                if repo_metrics.get("issue_type_stats"):
                    report.append(f"  Top Issue Types:")
                    type_stats = repo_metrics["issue_type_stats"]
                    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["percentage"], reverse=True)[:3]
                    for issue_type, stats in sorted_types:
                        report.append(f"    {issue_type.title()}: {stats['percentage']:.1f}%")

        # Overall statistics
        if results.get("overall_metrics", {}).get("review_time_stats"):
            overall = results["overall_metrics"]
            report.append(f"\n=== Overall Statistics ===")

            if overall.get("review_time_stats"):
                stats = overall["review_time_stats"]
                report.append(f"Review Time:")
                report.append(f"  Average: {stats['mean']:.2f} hours")
                report.append(f"  Min: {stats['min']:.2f}h, Max: {stats['max']:.2f}h")

            if overall.get("comment_stats"):
                stats = overall["comment_stats"]
                report.append(f"Comments:")
                report.append(f"  Average: {stats['mean']:.2f} comments")
                report.append(f"  Min: {stats['min']} comments, Max: {stats['max']} comments")

            if overall.get("issue_type_stats"):
                report.append(f"Issue Types:")
                type_stats = overall["issue_type_stats"]
                sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["percentage"], reverse=True)
                for issue_type, stats in sorted_types:
                    report.append(f"  {issue_type.title()}: {stats['percentage']:.1f}% ({stats['count']} PRs)")

        # Period breakdown
        if results.get("periods"):
            report.append(f"\n=== Period Breakdown ===")

            for period_result in results["periods"]:
                period_name = period_result["period_name"]
                metrics = period_result["metrics"]

                report.append(f"\n{period_name}:")
                report.append(f"  PRs with reviews: {metrics['prs_with_reviews']}")

                if metrics.get("review_time_stats"):
                    stats = metrics["review_time_stats"]
                    report.append(f"  Review Time:")
                    report.append(f"    Average: {stats['mean']:.2f} hours")
                    report.append(f"    Min: {stats['min']:.2f}h, Max: {stats['max']:.2f}h")

                if metrics.get("comment_stats"):
                    stats = metrics["comment_stats"]
                    report.append(f"  Comments:")
                    report.append(f"    Average: {stats['mean']:.2f} comments")
                    report.append(f"    Min: {stats['min']} comments, Max: {stats['max']} comments")

                if metrics.get("issue_type_stats"):
                    report.append(f"  Issue Types:")
                    type_stats = metrics["issue_type_stats"]
                    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["percentage"], reverse=True)
                    for issue_type, stats in sorted_types:
                        report.append(f"    {issue_type.title()}: {stats['percentage']:.1f}% ({stats['count']} PRs)")

                # Show individual PRs
                if metrics.get("pr_details"):
                    report.append(f"  PR Details:")
                    for pr_detail in metrics["pr_details"][:10]:  # Show first 10
                        review_time_str = f"{pr_detail['review_time_hours']:.2f}h" if pr_detail['review_time_hours'] is not None else "No review"
                        issue_type = pr_detail.get('issue_type', 'unknown')
                        report.append(
                            f"    PR #{pr_detail['number']}: "
                            f"{review_time_str} review time, "
                            f"{pr_detail['comment_count']} comments, "
                            f"Type: {issue_type}"
                        )
                        report.append(f"      by {pr_detail['user']} - {pr_detail['title'][:60]}...")

        return "\n".join(report)

    def generate_github_detailed_report(self, results: dict[str, Any]) -> str:
        """Generate a detailed report with all PR information."""
        report = []
        report.append(f"\n=== Detailed GitHub PR Analysis Report ===")

        # Handle both single and multi-repository results
        if "repositories" in results:
            report.append(f"Owner: {results['owner']}")
            report.append(f"Repositories: {', '.join(results['repositories'])}")
        else:
            # Backward compatibility
            report.append(f"Repository: {results.get('repository', 'Unknown')}")

        # Add configuration info
        self._add_config_to_report(report, results)

        overall = results.get("overall_metrics", {})
        if overall.get("pr_details"):
            report.append(f"\n=== All PRs with Review Details ===")

            # Sort PRs by review time (longest first)
            sorted_prs = sorted(
                overall["pr_details"],
                key=lambda x: x["review_time_hours"],
                reverse=True
            )

            for pr_detail in sorted_prs:
                report.append(
                    f"\nPR #{pr_detail['number']}: {pr_detail['title']}"
                )
                report.append(f"  Author: {pr_detail['user']}")
                report.append(f"  Created: {pr_detail['created_at']}")
                report.append(f"  Review Time: {pr_detail['review_time_hours']:.2f} hours")
                report.append(f"  Comments: {pr_detail['comment_count']}")

        return "\n".join(report)

    def _get_prs_for_repository(self, repo_name: str, target_branch: str = "develop") -> list:
        """Get PRs for a specific repository without modifying client state."""
        # Store original repo
        original_repo = self.github.repo

        try:
            # Temporarily set repo for this operation
            self.github.repo = repo_name
            return self.pr_service.get_pull_requests_with_pagination(
                state="closed", target_branch=target_branch
            )
        finally:
            # Always restore original repo
            self.github.repo = original_repo

    def _analyze_prs_for_repository(self, prs: list, repo_name: str) -> dict[str, Any]:
        """Analyze PRs for a specific repository."""
        # Store original repo
        original_repo = self.github.repo

        try:
            # Set repo for this operation and keep it set during the entire analysis
            self.github.repo = repo_name
            self.logger.debug(f"Analyzing {len(prs)} PRs for repository {repo_name}")

            # This will now use the correct repository context for all API calls
            return self.pr_service.analyze_pr_review_metrics(prs)
        except Exception as e:
            self.logger.error(f"Error analyzing PRs for repository {repo_name}: {e}")
            return {
                "total_prs": len(prs),
                "prs_with_reviews": 0,
                "review_times": [],
                "comment_counts": [],
                "pr_details": [],
            }
        finally:
            # Always restore original repo
            self.github.repo = original_repo

    def _aggregate_period_metrics_from_repos(self, repo_breakdowns: list, grouping: str) -> list:
        """Aggregate period metrics from individual repository analyses."""
        from collections import defaultdict
        from dateutil import parser

        period_aggregates = defaultdict(lambda: {
            "total_prs": 0,
            "prs_with_reviews": 0,
            "review_times": [],
            "comment_counts": [],
            "pr_details": [],
            "issue_types": {}
        })

        # Collect all PRs from all repositories and group by period
        for repo_result in repo_breakdowns:
            repo_metrics = repo_result.get("metrics", {})
            repo_pr_details = repo_metrics.get("pr_details", [])

            for pr_detail in repo_pr_details:
                try:
                    # Parse PR creation date and get period
                    if isinstance(pr_detail["created_at"], str):
                        created_at = parser.parse(pr_detail["created_at"])
                    else:
                        created_at = pr_detail["created_at"]

                    period_key = self.pr_service._get_period_key(created_at, grouping)

                    # Add to period aggregate
                    period_aggregates[period_key]["total_prs"] += 1
                    if pr_detail["review_time_hours"] is not None:
                        period_aggregates[period_key]["prs_with_reviews"] += 1
                        period_aggregates[period_key]["review_times"].append(pr_detail["review_time_hours"])

                    period_aggregates[period_key]["comment_counts"].append(pr_detail["comment_count"])
                    period_aggregates[period_key]["pr_details"].append(pr_detail)

                    # Track issue types
                    issue_type = pr_detail.get("issue_type", "other")
                    period_aggregates[period_key]["issue_types"][issue_type] = period_aggregates[period_key]["issue_types"].get(issue_type, 0) + 1

                except Exception as e:
                    self.logger.error(f"Error aggregating PR detail: {e}")
                    continue

        # Convert to final format
        periods = []
        for period_key, data in period_aggregates.items():
            # Calculate statistics for this period
            import statistics

            period_metrics = {
                "total_prs": data["total_prs"],
                "prs_with_reviews": data["prs_with_reviews"],
                "review_times": data["review_times"],
                "comment_counts": data["comment_counts"],
                "pr_details": data["pr_details"],
                "issue_types": data["issue_types"]
            }

            # Add statistics if we have data
            if data["review_times"]:
                period_metrics["review_time_stats"] = {
                    "mean": statistics.mean(data["review_times"]),
                    "min": min(data["review_times"]),
                    "max": max(data["review_times"]),
                    "count": len(data["review_times"])
                }

            if data["comment_counts"]:
                period_metrics["comment_stats"] = {
                    "mean": statistics.mean(data["comment_counts"]),
                    "min": min(data["comment_counts"]),
                    "max": max(data["comment_counts"]),
                    "count": len(data["comment_counts"])
                }

            # Calculate issue type percentages for this period
            if data["issue_types"]:
                total_period_prs = sum(data["issue_types"].values())
                period_metrics["issue_type_stats"] = {}
                for issue_type, count in data["issue_types"].items():
                    percentage = (count / total_period_prs) * 100
                    period_metrics["issue_type_stats"][issue_type] = {
                        "count": count,
                        "percentage": percentage
                    }

            periods.append({
                "period_key": period_key,
                "period_name": self.pr_service.format_period_name(period_key),
                "metrics": period_metrics
            })

        return periods

    def _aggregate_overall_metrics_from_repos(self, repo_breakdowns: list) -> dict[str, Any]:
        """Aggregate overall metrics from individual repository analyses."""
        import statistics

        all_review_times = []
        all_comment_counts = []
        all_pr_details = []
        all_issue_types = {}
        total_prs = 0
        total_with_reviews = 0

        for repo_result in repo_breakdowns:
            repo_metrics = repo_result.get("metrics", {})

            # Aggregate data
            total_prs += repo_result.get("total_prs", 0)
            total_with_reviews += repo_result.get("prs_with_reviews", 0)

            if repo_metrics.get("review_times"):
                all_review_times.extend(repo_metrics["review_times"])
            if repo_metrics.get("comment_counts"):
                all_comment_counts.extend(repo_metrics["comment_counts"])
            if repo_metrics.get("pr_details"):
                all_pr_details.extend(repo_metrics["pr_details"])
            if repo_metrics.get("issue_types"):
                for issue_type, count in repo_metrics["issue_types"].items():
                    all_issue_types[issue_type] = all_issue_types.get(issue_type, 0) + count

        # Build overall metrics
        overall_metrics = {
            "total_prs": total_prs,
            "prs_with_reviews": total_with_reviews,
            "review_times": all_review_times,
            "comment_counts": all_comment_counts,
            "pr_details": all_pr_details,
            "issue_types": all_issue_types
        }

        # Add statistics
        if all_review_times:
            overall_metrics["review_time_stats"] = {
                "mean": statistics.mean(all_review_times),
                "min": min(all_review_times),
                "max": max(all_review_times),
                "count": len(all_review_times)
            }

        if all_comment_counts:
            overall_metrics["comment_stats"] = {
                "mean": statistics.mean(all_comment_counts),
                "min": min(all_comment_counts),
                "max": max(all_comment_counts),
                "count": len(all_comment_counts)
            }

        # Calculate issue type percentages
        if all_issue_types:
            total_prs_for_types = sum(all_issue_types.values())
            overall_metrics["issue_type_stats"] = {}
            for issue_type, count in all_issue_types.items():
                percentage = (count / total_prs_for_types) * 100
                overall_metrics["issue_type_stats"][issue_type] = {
                    "count": count,
                    "percentage": percentage
                }

        return overall_metrics

    def _add_config_to_report(self, report: list[str], results: dict[str, Any]) -> None:
        """Add configuration info to report."""
        if results.get("config_used"):
            config = results["config_used"]
            report.append("Configuration:")

            if config.get("grouping"):
                report.append(f"  Grouping: {config['grouping']}")

            if config.get("start_date") or config.get("end_date"):
                date_range = []
                if config.get("start_date"):
                    date_range.append(f"from {config['start_date']}")
                if config.get("end_date"):
                    date_range.append(f"to {config['end_date']}")
                report.append(f"  Date Range: {' '.join(date_range)}")

            if config.get("target_branch"):
                report.append(f"  Target Branch: {config['target_branch']}")