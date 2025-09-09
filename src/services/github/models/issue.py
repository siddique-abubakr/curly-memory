"""
GitHub issue models for the /issues endpoints.

These models represent issue data returned by GitHub's REST API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .base import GitHubUser, GitHubLabel, GitHubMilestone
from .repository import Repository


class IssueState(str, Enum):
    """Issue states"""

    OPEN = "open"
    CLOSED = "closed"


class IssueStateReason(str, Enum):
    """Issue state change reasons"""

    COMPLETED = "completed"
    NOT_PLANNED = "not_planned"
    REOPENED = "reopened"


class IssuePullRequest(BaseModel):
    """Pull request reference in issue (indicates issue is actually a pull request)"""

    url: HttpUrl = Field(description="API URL for pull request")
    html_url: HttpUrl = Field(description="GitHub URL for pull request")
    diff_url: HttpUrl = Field(description="Diff URL for pull request")
    patch_url: HttpUrl = Field(description="Patch URL for pull request")
    merged_at: Optional[datetime] = Field(
        default=None, description="Pull request merge date"
    )


class IssueReactions(BaseModel):
    """Issue reaction counts"""

    url: HttpUrl = Field(description="API URL for reactions")
    total_count: int = Field(description="Total reaction count")
    plus_one: int = Field(alias="+1", description="👍 reactions")
    minus_one: int = Field(alias="-1", description="👎 reactions")
    laugh: int = Field(description="😄 reactions")
    hooray: int = Field(description="🎉 reactions")
    confused: int = Field(description="😕 reactions")
    heart: int = Field(description="❤️ reactions")
    rocket: int = Field(description="🚀 reactions")
    eyes: int = Field(description="👀 reactions")


class Issue(BaseModel):
    """GitHub issue model for API responses"""

    id: int = Field(description="Unique issue ID")
    node_id: str = Field(description="GraphQL node ID")
    url: HttpUrl = Field(description="API URL for issue")
    repository_url: HttpUrl = Field(description="API URL for repository")
    labels_url: str = Field(description="URL template for issue labels")
    comments_url: HttpUrl = Field(description="API URL for issue comments")
    events_url: HttpUrl = Field(description="API URL for issue events")
    html_url: HttpUrl = Field(description="GitHub URL for issue")
    number: int = Field(description="Issue number")
    state: IssueState = Field(description="Issue state")
    state_reason: Optional[IssueStateReason] = Field(
        default=None, description="Reason for state change"
    )
    title: str = Field(description="Issue title")
    body: Optional[str] = Field(default=None, description="Issue body/description")
    user: GitHubUser = Field(description="User who created the issue")
    labels: List[GitHubLabel] = Field(description="Labels attached to issue")
    assignee: Optional[GitHubUser] = Field(default=None, description="Assigned user")
    assignees: List[GitHubUser] = Field(description="All assigned users")
    milestone: Optional[GitHubMilestone] = Field(
        default=None, description="Associated milestone"
    )
    locked: bool = Field(description="Whether issue is locked")
    active_lock_reason: Optional[str] = Field(
        default=None, description="Reason for locking if locked"
    )
    comments: int = Field(description="Number of comments on issue")
    pull_request: Optional[IssuePullRequest] = Field(
        default=None, description="Pull request info (if issue is a PR)"
    )
    closed_at: Optional[datetime] = Field(default=None, description="Issue close date")
    created_at: datetime = Field(description="Issue creation date")
    updated_at: datetime = Field(description="Last issue update")
    closed_by: Optional[GitHubUser] = Field(
        default=None, description="User who closed the issue"
    )
    author_association: str = Field(description="Author's association with repository")
    body_html: Optional[str] = Field(
        default=None, description="Issue body rendered as HTML"
    )
    body_text: Optional[str] = Field(
        default=None, description="Issue body as plain text"
    )
    timeline_url: Optional[HttpUrl] = Field(
        default=None, description="API URL for issue timeline"
    )
    repository: Optional[Repository] = Field(
        default=None, description="Repository containing the issue"
    )
    performed_via_github_app: Optional[Dict[str, Any]] = Field(
        default=None, description="GitHub App that performed action"
    )
    reactions: Optional[IssueReactions] = Field(
        default=None, description="Issue reactions"
    )


class IssueComment(BaseModel):
    """GitHub issue comment model"""

    id: int = Field(description="Comment ID")
    node_id: str = Field(description="GraphQL node ID")
    url: HttpUrl = Field(description="API URL for comment")
    html_url: HttpUrl = Field(description="GitHub URL for comment")
    body: str = Field(description="Comment body")
    user: GitHubUser = Field(description="User who created the comment")
    created_at: datetime = Field(description="Comment creation date")
    updated_at: datetime = Field(description="Last comment update")
    issue_url: HttpUrl = Field(description="API URL for associated issue")
    author_association: str = Field(description="Author's association with repository")
    body_html: Optional[str] = Field(
        default=None, description="Comment body rendered as HTML"
    )
    body_text: Optional[str] = Field(
        default=None, description="Comment body as plain text"
    )
    reactions: Optional[IssueReactions] = Field(
        default=None, description="Comment reactions"
    )
    performed_via_github_app: Optional[Dict[str, Any]] = Field(
        default=None, description="GitHub App that performed action"
    )
