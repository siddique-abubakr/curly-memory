from core import constants
from core.logger import Logger
import requests
from typing import Union, List
from .github_params import (
    CommitParams,
    PullRequestParams,
    IssueParams,
    ContributorParams,
    BranchParams,
    ReleaseParams,
    PullRequestCommitsParams,
    PullRequestReviewsParams,
)
from services.github.models import (
    Repository,
    Commit,
    CommitDetails,
    PullRequest,
    Issue,
    Contributor,
    Branch,
    Release,
)


class GithubClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GithubClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.headers = constants.GITHUB_CONFIG.get("headers")
            self.logger = Logger.get_logger()
            self.base_url = "https://api.github.com"
            self.owner = constants.GITHUB_CONFIG.get("owner")
            self.repo = constants.GITHUB_CONFIG.get("repo")
            self._initialized = True

    def _make_request(self, endpoint: str, params: dict = None) -> dict | list:
        """Make a GET request to GitHub API endpoint"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error making GET request to {url}: {e}")
            return {} if "list" not in endpoint else []

    def get_repository(self) -> Repository | None:
        """GET /repos/{owner}/{repo}

        Gets repository information including description, stars, forks, etc.

        Returns:
            Repository object with all repository information, or None if request fails

        Example:
            repo = client.get_repository()
            if repo:
                print(f"Repository: {repo.full_name}")
                print(f"Stars: {repo.stargazers_count}")
        """
        response = self._make_request("")
        if response:
            try:
                return Repository(**response)
            except Exception as e:
                self.logger.error(f"Error parsing repository response: {e}")
                return None
        return None

    def get_commits(
        self, params: Union[CommitParams, dict, None] = None
    ) -> List[Commit]:
        """GET /repos/{owner}/{repo}/commits

        Args:
            params: CommitParams model or dict with query parameters

        Returns:
            List of Commit objects with commit information

        Example:
            # Using parameter model (recommended)
            params = CommitParams(
                since="2024-01-01T00:00:00Z",
                author="username",
                per_page=50
            )
            commits = client.get_commits(params)
            for commit in commits:
                print(f"Commit: {commit.sha} by {commit.commit.author.name}")

            # Using dict (legacy)
            commits = client.get_commits({"since": "2024-01-01T00:00:00Z"})
        """
        if isinstance(params, CommitParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("commits", params)
        if isinstance(response, list):
            try:
                return [Commit(**commit_data) for commit_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing commits response: {e}")
                return []
        return []

    def get_pull_requests(
        self, params: Union[PullRequestParams, dict, None] = None
    ) -> List[PullRequest]:
        """GET /repos/{owner}/{repo}/pulls

        Args:
            params: PullRequestParams model or dict with query parameters

        Returns:
            List of PullRequest objects with pull request information

        Example:
            # Using parameter model (recommended)
            params = PullRequestParams(
                state=PullRequestState.ALL,
                sort=PullRequestSort.UPDATED,
                per_page=100
            )
            prs = client.get_pull_requests(params)
            for pr in prs:
                print(f"PR #{pr.number}: {pr.title} ({pr.state})")
        """
        if isinstance(params, PullRequestParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("pulls", params)
        if isinstance(response, list):
            try:
                return [PullRequest(**pr_data) for pr_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing pull requests response: {e}")
                return []
        return []

    def get_issues(self, params: Union[IssueParams, dict, None] = None) -> List[Issue]:
        """GET /repos/{owner}/{repo}/issues

        Args:
            params: IssueParams model or dict with query parameters

        Returns:
            List of Issue objects with issue information

        Example:
            # Using parameter model (recommended)
            params = IssueParams(
                state=IssueState.ALL,
                labels="bug,enhancement",
                sort=IssueSort.UPDATED
            )
            issues = client.get_issues(params)
            for issue in issues:
                print(f"Issue #{issue.number}: {issue.title} ({issue.state})")
        """
        if isinstance(params, IssueParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("issues", params)
        if isinstance(response, list):
            try:
                return [Issue(**issue_data) for issue_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing issues response: {e}")
                return []
        return []

    def get_branches(
        self, params: Union[BranchParams, dict, None] = None
    ) -> List[Branch]:
        """GET /repos/{owner}/{repo}/branches

        Args:
            params: BranchParams model or dict with query parameters

        Returns:
            List of Branch objects with branch information

        Example:
            # Using parameter model (recommended)
            params = BranchParams(protected=True, per_page=50)
            branches = client.get_branches(params)
            for branch in branches:
                print(f"Branch: {branch.name} (protected: {branch.protected})")
        """
        if isinstance(params, BranchParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("branches", params)
        if isinstance(response, list):
            try:
                return [Branch(**branch_data) for branch_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing branches response: {e}")
                return []
        return []

    def get_contributors(
        self, params: Union[ContributorParams, dict, None] = None
    ) -> List[Contributor]:
        """GET /repos/{owner}/{repo}/contributors

        Args:
            params: ContributorParams model or dict with query parameters

        Returns:
            List of Contributor objects with contributor information

        Example:
            # Using parameter model (recommended)
            params = ContributorParams(anon=True, per_page=100)
            contributors = client.get_contributors(params)
            for contributor in contributors:
                print(f"Contributor: {contributor.login}
                ({contributor.contributions} contributions)")
        """
        if isinstance(params, ContributorParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("contributors", params)
        if isinstance(response, list):
            try:
                return [
                    Contributor(**contributor_data) for contributor_data in response
                ]
            except Exception as e:
                self.logger.error(f"Error parsing contributors response: {e}")
                return []
        return []

    def get_releases(
        self, params: Union[ReleaseParams, dict, None] = None
    ) -> List[Release]:
        """GET /repos/{owner}/{repo}/releases

        Args:
            params: ReleaseParams model or dict with query parameters

        Returns:
            List of Release objects with release information

        Example:
            # Using parameter model (recommended)
            params = ReleaseParams(per_page=100, page=1)
            releases = client.get_releases(params)
            for release in releases:
                print(f"Release: {release.tag_name} ({release.name})")
        """
        if isinstance(params, ReleaseParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request("releases", params)
        if isinstance(response, list):
            try:
                return [Release(**release_data) for release_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing releases response: {e}")
                return []
        return []

    def get_commit(self, sha: str) -> CommitDetails | None:
        """GET /repos/{owner}/{repo}/commits/{sha}

        Args:
            sha: The commit SHA hash

        Returns:
            CommitDetails object with detailed commit information,
            or None if request fails

        Example:
            commit = client.get_commit("abc123def456")
            if commit:
                print(f"Author: {commit.commit.author.name}")
                print(f"Files changed: {len(commit.files) if commit.files else 0}")
        """
        response = self._make_request(f"commits/{sha}")
        if response:
            try:
                return CommitDetails(**response)
            except Exception as e:
                self.logger.error(f"Error parsing commit response: {e}")
                return None
        return None

    def get_pull_request(self, number: int) -> PullRequest | None:
        """GET /repos/{owner}/{repo}/pulls/{number}

        Args:
            number: Pull request number

        Returns:
            PullRequest object with detailed pull request information,
            or None if request fails

        Example:
            pr = client.get_pull_request(123)
            if pr:
                print(f"PR Title: {pr.title}")
                print(f"State: {pr.state}")
                print(f"Mergeable: {pr.mergeable}")
        """
        response = self._make_request(f"pulls/{number}")
        if response:
            try:
                return PullRequest(**response)
            except Exception as e:
                self.logger.error(f"Error parsing pull request response: {e}")
                return None
        return None

    def get_issue(self, number: int) -> Issue | None:
        """GET /repos/{owner}/{repo}/issues/{number}

        Args:
            number: Issue number

        Returns:
            Issue object with detailed issue information, or None if request fails

        Example:
            issue = client.get_issue(456)
            if issue:
                print(f"Issue Title: {issue.title}")
                print(f"Labels: {[label.name for label in issue.labels]}")
                print(f"State: {issue.state}")
        """
        response = self._make_request(f"issues/{number}")
        if response:
            try:
                return Issue(**response)
            except Exception as e:
                self.logger.error(f"Error parsing issue response: {e}")
                return None
        return None

    def get_pull_request_commits(
        self, number: int, params: Union[PullRequestCommitsParams, dict, None] = None
    ) -> List[Commit]:
        """GET /repos/{owner}/{repo}/pulls/{number}/commits

        Args:
            number: Pull request number
            params: PullRequestCommitsParams model or dict with query parameters

        Returns:
            List of Commit objects for the pull request

        Example:
            # Using parameter model (recommended)
            params = PullRequestCommitsParams(per_page=100, page=1)
            commits = client.get_pull_request_commits(123, params)
            for commit in commits:
                print(f"Commit: {commit.sha} - {commit.commit.message}")
        """
        if isinstance(params, PullRequestCommitsParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request(f"pulls/{number}/commits", params)
        if isinstance(response, list):
            try:
                return [Commit(**commit_data) for commit_data in response]
            except Exception as e:
                self.logger.error(f"Error parsing pull request commits response: {e}")
                return []
        return []

    def get_pull_request_reviews(
        self, number: int, params: Union[PullRequestReviewsParams, dict, None] = None
    ) -> List[dict]:
        """GET /repos/{owner}/{repo}/pulls/{number}/reviews

        Args:
            number: Pull request number
            params: PullRequestReviewsParams model or dict with query parameters

        Returns:
            List of pull request review data (raw dict for now)

        Example:
            # Using parameter model (recommended)
            params = PullRequestReviewsParams(per_page=50, page=1)
            reviews = client.get_pull_request_reviews(123, params)
            for review in reviews:
                print(f"Review by {review['user']['login']}: {review['state']}")
        """
        if isinstance(params, PullRequestReviewsParams):
            params = params.model_dump(exclude_none=True)
        response = self._make_request(f"pulls/{number}/reviews", params)
        if isinstance(response, list):
            return response
        return []
