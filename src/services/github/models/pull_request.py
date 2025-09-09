"""
GitHub pull request models for the /pulls endpoints.

These models represent pull request data returned by GitHub's REST API.
"""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .base import GitHubUser, GitHubLabel, GitHubMilestone, GitHubBranch
from .repository import Repository


class PullRequestState(str, Enum):
    """Pull request states"""

    OPEN = "open"
    CLOSED = "closed"


class PullRequestMergeableState(str, Enum):
    """Pull request mergeable states"""

    MERGEABLE = "mergeable"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


class AutoMerge(BaseModel):
    """Auto merge configuration"""

    enabled_by: GitHubUser = Field(description="User who enabled auto-merge")
    merge_method: str = Field(description="Merge method (merge, squash, rebase)")
    commit_title: str | None = Field(default=None, description="Commit title for merge")
    commit_message: str | None = Field(
        default=None, description="Commit message for merge"
    )


class PullRequestHead(GitHubBranch):
    """Pull request head branch (extends GitHubBranch with repository info)"""

    repo: "Repository | None" = Field(
        default=None, description="Repository containing the head branch"
    )


class PullRequestBase(GitHubBranch):
    """Pull request base branch (extends GitHubBranch with repository info)"""

    repo: Repository = Field(description="Repository containing the base branch")


class PullRequestLinks(BaseModel):
    """Pull request hypermedia links"""

    self: dict[str, str] = Field(description="Link to pull request")
    html: dict[str, str] = Field(description="Link to pull request on GitHub")
    issue: dict[str, str] = Field(description="Link to associated issue")
    comments: dict[str, str] = Field(description="Link to pull request comments")
    review_comments: dict[str, str] = Field(description="Link to review comments")
    review_comment: dict[str, str] = Field(
        description="Link template for review comments"
    )
    commits: dict[str, str] = Field(description="Link to pull request commits")
    statuses: dict[str, str] = Field(description="Link to commit statuses")


class PullRequest(BaseModel):
    """GitHub pull request model for API responses"""

    url: HttpUrl = Field(description="API URL for pull request")
    id: int = Field(description="Unique pull request ID")
    node_id: str = Field(description="GraphQL node ID")
    html_url: HttpUrl = Field(description="GitHub URL for pull request")
    diff_url: HttpUrl = Field(description="Diff URL for pull request")
    patch_url: HttpUrl = Field(description="Patch URL for pull request")
    issue_url: HttpUrl = Field(description="API URL for associated issue")
    commits_url: HttpUrl = Field(description="API URL for pull request commits")
    review_comments_url: HttpUrl = Field(description="API URL for review comments")
    review_comment_url: str = Field(
        description="URL template for individual review comment"
    )
    comments_url: HttpUrl = Field(description="API URL for issue comments")
    statuses_url: HttpUrl = Field(description="API URL for commit statuses")
    number: int = Field(description="Pull request number")
    state: PullRequestState = Field(description="Pull request state")
    locked: bool = Field(description="Whether pull request is locked")
    title: str = Field(description="Pull request title")
    body: str | None = Field(default=None, description="Pull request body/description")
    user: GitHubUser = Field(description="User who created the pull request")
    labels: list[GitHubLabel] = Field(description="Labels attached to pull request")
    milestone: GitHubMilestone | None = Field(
        default=None, description="Associated milestone"
    )
    active_lock_reason: str | None = Field(
        default=None, description="Reason for locking if locked"
    )
    created_at: datetime = Field(description="Pull request creation date")
    updated_at: datetime = Field(description="Last pull request update")
    closed_at: datetime | None = Field(
        default=None, description="Pull request close date"
    )
    merged_at: datetime | None = Field(
        default=None, description="Pull request merge date"
    )
    merge_commit_sha: str | None = Field(
        default=None, description="SHA of merge commit"
    )
    assignee: GitHubUser | None = Field(default=None, description="Assigned user")
    assignees: list[GitHubUser] = Field(description="All assigned users")
    requested_reviewers: list[GitHubUser] = Field(description="Requested reviewers")
    requested_teams: list[dict[str, any]] = Field(
        description="Requested reviewer teams"
    )
    head: PullRequestHead = Field(description="Head branch information")
    base: PullRequestBase = Field(description="Base branch information")
    _links: PullRequestLinks = Field(alias="_links", description="Hypermedia links")
    author_association: str = Field(description="Author's association with repository")
    auto_merge: AutoMerge | None = Field(
        default=None, description="Auto merge settings"
    )
    draft: bool = Field(description="Whether pull request is a draft")

    # Extended fields (only available in single pull request endpoint)
    mergeable: bool | None = Field(
        default=None, description="Whether pull request can be merged"
    )
    rebaseable: bool | None = Field(
        default=None, description="Whether pull request can be rebased"
    )
    mergeable_state: PullRequestMergeableState | None = Field(
        default=None, description="Mergeable state"
    )
    merged_by: GitHubUser | None = Field(
        default=None, description="User who merged the pull request"
    )
    comments: int | None = Field(default=None, description="Number of issue comments")
    review_comments: int | None = Field(
        default=None, description="Number of review comments"
    )
    maintainer_can_modify: bool | None = Field(
        default=None, description="Whether maintainers can modify"
    )
    commits: int | None = Field(default=None, description="Number of commits")
    additions: int | None = Field(default=None, description="Number of additions")
    deletions: int | None = Field(default=None, description="Number of deletions")
    changed_files: int | None = Field(
        default=None, description="Number of changed files"
    )


class PullRequestReviewState(str, Enum):
    """Pull request review states"""

    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    DISMISSED = "DISMISSED"
    PENDING = "PENDING"


class PullRequestReview(BaseModel):
    """Pull request review model"""

    id: int = Field(description="Review ID")
    node_id: str = Field(description="GraphQL node ID")
    user: GitHubUser = Field(description="User who submitted the review")
    body: str | None = Field(default=None, description="Review body text")
    state: PullRequestReviewState = Field(description="Review state")
    html_url: HttpUrl = Field(description="GitHub URL for review")
    pull_request_url: HttpUrl = Field(description="API URL for associated pull request")
    author_association: str = Field(description="Author's association with repository")
    _links: dict[str, dict[str, str]] = Field(
        alias="_links", description="Hypermedia links"
    )
    submitted_at: datetime | None = Field(
        default=None, description="Review submission date"
    )
    commit_id: str = Field(description="Commit SHA that was reviewed")
