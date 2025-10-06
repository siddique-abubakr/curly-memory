"""
GitHub API response models for type safety and validation.

This module provides Pydantic models that match GitHub's REST API v3 response schemas.
These models ensure type safety and provide clear documentation of
expected response structures.
"""

from .base import GitHubUser, GitHubLabel, GitHubMilestone, GitHubBranch
from .repository import (
    Repository,
    RepositoryOwner,
    RepositoryPermissions,
    SecurityAnalysis,
)
from .commit import (
    Commit,
    CommitDetails,
    CommitAuthor,
    GitCommit,
    GitTree,
    CommitVerification,
    CommitParent,
)
from .pull_request import PullRequest, PullRequestHead, PullRequestBase
from .issue import Issue, IssuePullRequest
from .contributor import Contributor, Branch
from .release import Release, ReleaseAsset, ReleaseAuthor

__all__ = [
    # Base models
    "GitHubUser",
    "GitHubLabel",
    "GitHubMilestone",
    "GitHubBranch",
    # Repository models
    "Repository",
    "RepositoryOwner",
    "RepositoryPermissions",
    "SecurityAnalysis",
    # Commit models
    "Commit",
    "CommitDetails",
    "CommitAuthor",
    "GitCommit",
    "GitTree",
    "CommitVerification",
    "CommitParent",
    # Pull request models
    "PullRequest",
    "PullRequestHead",
    "PullRequestBase",
    # Issue models
    "Issue",
    "IssuePullRequest",
    # Contributor models
    "Contributor",
    "Branch",
    # Release models
    "Release",
    "ReleaseAsset",
    "ReleaseAuthor",
]
