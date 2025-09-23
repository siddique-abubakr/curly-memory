from datetime import datetime
from dateutil import parser
from collections import defaultdict
import statistics
from typing import Any

from core.logger import Logger
from clients.github_params import PullRequestParams
from services.github.models import PullRequest


class PRService:
    """Service class for handling GitHub pull request operations."""

    def __init__(self, github_client):
        self.github = github_client
        self.logger = Logger.get_logger()

    def get_pull_requests_with_pagination(
        self, state: str = "closed", target_branch: str = "develop"
    ) -> list[PullRequest]:
        """Get all pull requests with pagination support."""
        all_prs = []
        page = 1
        per_page = 100

        while True:
            try:
                params = PullRequestParams(
                    state=state, per_page=per_page, page=page, base=target_branch
                )
                prs_page = self.github.get_pull_requests(params)

                if not prs_page:
                    break

                all_prs.extend(prs_page)
                page += 1

                self.logger.debug(
                    f"Fetched page {page-1}, PRs: {len(prs_page)}, "
                    f"Total: {len(all_prs)}"
                )

                # If we got fewer results than per_page, we've reached the end
                if len(prs_page) < per_page:
                    break

            except Exception as e:
                self.logger.error(f"Error fetching PRs page {page}: {e}")
                break

        self.logger.info(f"Total PRs fetched: {len(all_prs)}")
        return all_prs

    def get_pr_metrics_batch(self, pr_number: int) -> tuple[datetime | None, int]:
        """Get both review time and comment count in a single batch to reduce API calls."""
        try:
            # Get reviews for review time
            reviews = self.github.get_pull_request_reviews(pr_number)
            first_review_time = None
            if reviews:
                self.logger.debug(f"PR #{pr_number} has {len(reviews)} reviews")
                first_review_time = parser.parse(reviews[0]["submitted_at"])

            # Get comments count - simplified approach using issue comments only for speed
            issue_response = self.github._make_request(f"issues/{pr_number}/comments")
            issue_comments = issue_response if isinstance(issue_response, list) else []
            comment_count = len(issue_comments)

            self.logger.debug(f"PR #{pr_number}: {comment_count} comments")
            return first_review_time, comment_count

        except Exception as e:
            self.logger.error(f"Error getting metrics for PR {pr_number}: {e}")
            return None, 0

    def get_first_review_time(self, pr_number: int) -> datetime | None:
        """Get the timestamp of the first review for a PR."""
        try:
            reviews = self.github.get_pull_request_reviews(pr_number)
            if not reviews:
                return None

            self.logger.debug(f"PR #{pr_number} has {len(reviews)} reviews")
            return parser.parse(reviews[0]["submitted_at"])

        except Exception as e:
            self.logger.error(
                f"Error getting first review time for PR {pr_number}: {e}"
            )
            return None

    def get_pr_comments_count(self, pr_number: int) -> int:
        """Get total number of comments for a PR (issue + review comments)."""
        try:
            # GitHub API treats PRs as issues for comment endpoints
            issue_response = self.github._make_request(f"issues/{pr_number}/comments")
            issue_comments = issue_response if isinstance(issue_response, list) else []

            # Get review comments (line-specific comments)
            review_response = self.github._make_request(f"pulls/{pr_number}/comments")
            review_comments = review_response if isinstance(review_response, list) else []

            total_comments = len(issue_comments) + len(review_comments)
            self.logger.debug(
                f"PR #{pr_number}: {len(issue_comments)} issue + "
                f"{len(review_comments)} review = {total_comments} total comments"
            )

            return total_comments

        except Exception as e:
            self.logger.error(f"Error getting comment count for PR {pr_number}: {e}")
            return 0

    def filter_prs_by_date_range(
        self, prs: list[PullRequest], start_date: str = None, end_date: str = None
    ) -> list[PullRequest]:
        """Filter PRs by creation date range."""
        if not start_date and not end_date:
            return prs

        filtered_prs = []
        filtered_count = 0

        for pr in prs:
            try:
                # Validate PR has created_at field
                if not hasattr(pr, 'created_at') or not pr.created_at:
                    self.logger.warning(f"PR {pr.number} missing created_at field")
                    filtered_count += 1
                    continue

                # Handle both string and datetime objects for created_at
                if isinstance(pr.created_at, datetime):
                    created_at = pr.created_at
                elif isinstance(pr.created_at, str):
                    created_at = parser.parse(pr.created_at)
                else:
                    self.logger.error(f"PR {pr.number} has invalid created_at type: {type(pr.created_at)}")
                    filtered_count += 1
                    continue

                # Check date range
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        # Handle timezone awareness
                        if created_at.tzinfo is not None:
                            start_dt = start_dt.replace(tzinfo=created_at.tzinfo)
                        else:
                            # If created_at is naive, make start_dt naive too
                            start_dt = start_dt.replace(tzinfo=None)

                        if created_at < start_dt:
                            filtered_count += 1
                            continue
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"Error parsing start_date '{start_date}': {e}")
                        filtered_count += 1
                        continue

                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        # Handle timezone awareness
                        if created_at.tzinfo is not None:
                            end_dt = end_dt.replace(tzinfo=created_at.tzinfo)
                        else:
                            # If created_at is naive, make end_dt naive too
                            end_dt = end_dt.replace(tzinfo=None)

                        if created_at > end_dt:
                            filtered_count += 1
                            continue
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"Error parsing end_date '{end_date}': {e}")
                        filtered_count += 1
                        continue

                filtered_prs.append(pr)

            except Exception as e:
                self.logger.error(f"Error filtering PR {getattr(pr, 'number', 'unknown')}: {e}")
                filtered_count += 1

        self.logger.info(
            f"Filtered {len(filtered_prs)} PRs from {len(prs)} total "
            f"({filtered_count} filtered out)"
        )
        return filtered_prs

    def filter_prs_by_target_branch(
        self, prs: list[PullRequest], target_branch: str = "develop"
    ) -> list[PullRequest]:
        """Filter PRs by target branch."""
        filtered_prs = []
        filtered_count = 0

        for pr in prs:
            try:
                if pr.base and pr.base.ref == target_branch:
                    filtered_prs.append(pr)
                else:
                    filtered_count += 1
            except Exception as e:
                self.logger.error(f"Error checking target branch for PR {pr.number}: {e}")
                filtered_count += 1

        self.logger.info(
            f"Filtered {len(filtered_prs)} PRs targeting '{target_branch}' "
            f"from {len(prs)} total ({filtered_count} filtered out)"
        )
        return filtered_prs

    def analyze_issue_types(self, pr: PullRequest) -> str:
        """Analyze PR title and body to categorize issue type."""
        title = (pr.title or "").lower()
        body = (pr.body or "").lower()
        combined_text = f"{title} {body}"

        # Define keywords for different issue types
        issue_type_keywords = {
            "bug": ["fix", "bug", "error", "issue", "problem", "crash", "failure", "broken"],
            "feature": ["feat", "feature", "add", "new", "implement", "enhancement", "improve"],
            "style": ["style", "format", "lint", "whitespace", "indentation", "cleanup", "refactor"],
            "docs": ["doc", "documentation", "readme", "comment", "docstring"],
            "test": ["test", "testing", "spec", "unit", "integration"],
            "chore": ["chore", "update", "upgrade", "dependency", "deps", "version", "bump"],
            "performance": ["perf", "performance", "optimize", "speed", "fast", "slow"]
        }

        # Score each type based on keyword matches
        type_scores = {}
        for issue_type, keywords in issue_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                type_scores[issue_type] = score

        # Return the type with highest score, or "other" if no matches
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        return "other"

    def analyze_pr_review_metrics(
        self, prs: list[PullRequest]
    ) -> dict[str, Any]:
        """Analyze review time, comment metrics, and issue types for PRs."""
        metrics = {
            "total_prs": len(prs),
            "prs_with_reviews": 0,
            "review_times": [],
            "comment_counts": [],
            "pr_details": [],
            "issue_types": {},
        }

        for pr in prs:
            try:
                self.logger.debug(f"Analyzing PR #{pr.number}")

                # Analyze issue type for all PRs
                issue_type = self.analyze_issue_types(pr)
                metrics["issue_types"][issue_type] = metrics["issue_types"].get(issue_type, 0) + 1

                # Get metrics in batch to reduce API calls
                first_review_time, comment_count = self.get_pr_metrics_batch(pr.number)

                if first_review_time:
                    # Calculate review time in hours
                    # Handle both string and datetime objects for created_at
                    if isinstance(pr.created_at, datetime):
                        created_at = pr.created_at
                    elif isinstance(pr.created_at, str):
                        created_at = parser.parse(pr.created_at)
                    else:
                        self.logger.error(f"PR {pr.number} has invalid created_at type for review metrics: {type(pr.created_at)}")
                        continue

                    review_delta = (first_review_time - created_at).total_seconds() / 3600

                    # Store metrics for PRs with reviews
                    metrics["review_times"].append(review_delta)
                    metrics["comment_counts"].append(comment_count)
                    metrics["pr_details"].append({
                        "number": pr.number,
                        "title": pr.title,
                        "review_time_hours": review_delta,
                        "comment_count": comment_count,
                        "created_at": pr.created_at,
                        "user": pr.user.login if pr.user else "Unknown",
                        "issue_type": issue_type
                    })
                    metrics["prs_with_reviews"] += 1
                else:
                    # Store details for PRs without reviews too (for issue type analysis)
                    metrics["pr_details"].append({
                        "number": pr.number,
                        "title": pr.title,
                        "review_time_hours": None,
                        "comment_count": comment_count,
                        "created_at": pr.created_at,
                        "user": pr.user.login if pr.user else "Unknown",
                        "issue_type": issue_type
                    })

            except Exception as e:
                self.logger.error(f"Error analyzing PR {pr.number}: {e}")

        # Calculate statistics
        if metrics["review_times"]:
            metrics["review_time_stats"] = {
                "mean": statistics.mean(metrics["review_times"]),
                "min": min(metrics["review_times"]),
                "max": max(metrics["review_times"]),
                "count": len(metrics["review_times"])
            }

        if metrics["comment_counts"]:
            metrics["comment_stats"] = {
                "mean": statistics.mean(metrics["comment_counts"]),
                "min": min(metrics["comment_counts"]),
                "max": max(metrics["comment_counts"]),
                "count": len(metrics["comment_counts"])
            }

        # Calculate issue type percentages
        if metrics["issue_types"]:
            total_prs = sum(metrics["issue_types"].values())
            metrics["issue_type_stats"] = {}
            for issue_type, count in metrics["issue_types"].items():
                percentage = (count / total_prs) * 100
                metrics["issue_type_stats"][issue_type] = {
                    "count": count,
                    "percentage": percentage
                }

        return metrics

    def group_prs_by_period(
        self, prs: list[PullRequest], grouping: str = "monthly"
    ) -> dict[str, list[PullRequest]]:
        """Group PRs by time period (monthly or semi-monthly)."""
        periods = defaultdict(list)

        for pr in prs:
            try:
                # Handle both string and datetime objects for created_at
                if isinstance(pr.created_at, datetime):
                    created_at = pr.created_at
                elif isinstance(pr.created_at, str):
                    created_at = parser.parse(pr.created_at)
                else:
                    self.logger.error(f"PR {pr.number} has invalid created_at type for grouping: {type(pr.created_at)}")
                    continue

                period_key = self._get_period_key(created_at, grouping)
                periods[period_key].append(pr)
            except Exception as e:
                self.logger.error(f"Error grouping PR {pr.number}: {e}")

        return dict(periods)

    def _get_period_key(self, date: datetime, grouping: str) -> str:
        """Generate a period key based on the grouping method."""
        if grouping == "monthly":
            return f"{date.year}-{date.month:02d}"
        elif grouping == "semi-monthly":
            if date.day <= 15:
                return f"{date.year}-{date.month:02d}-H1"  # First half
            else:
                return f"{date.year}-{date.month:02d}-H2"  # Second half
        else:
            raise ValueError("Grouping must be 'monthly' or 'semi-monthly'")

    def format_period_name(self, period_key: str) -> str:
        """Convert period key to readable format."""
        if "-H1" in period_key or "-H2" in period_key:
            # Semi-monthly format
            parts = period_key.split("-")
            year, month = parts[0], parts[1]
            half = "1st half" if parts[2] == "H1" else "2nd half"
            month_name = datetime(int(year), int(month), 1).strftime("%B")
            return f"{month_name} {year} ({half})"
        else:
            # Monthly format
            year, month = period_key.split("-")
            month_name = datetime(int(year), int(month), 1).strftime("%B")
            return f"{month_name} {year}"
