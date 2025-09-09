"""
Base GitHub API models used across multiple endpoints.

These models represent common GitHub entities that appear in various API responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .repository import Repository


class UserType(str, Enum):
    """GitHub user types"""

    USER = "User"
    BOT = "Bot"
    ORGANIZATION = "Organization"


class GitHubUser(BaseModel):
    """GitHub user/organization model used across API responses"""

    login: str = Field(description="Username or organization name")
    id: int = Field(description="Unique user ID")
    node_id: str = Field(description="GraphQL node ID")
    avatar_url: HttpUrl = Field(description="User's avatar image URL")
    gravatar_id: str | None = Field(default=None, description="Gravatar ID")
    url: HttpUrl = Field(description="API URL for user")
    html_url: HttpUrl = Field(description="GitHub profile URL")
    followers_url: HttpUrl = Field(description="API URL for followers")
    following_url: str = Field(description="API URL template for following")
    gists_url: str = Field(description="API URL template for gists")
    starred_url: str = Field(description="API URL template for starred repos")
    subscriptions_url: HttpUrl = Field(description="API URL for subscriptions")
    organizations_url: HttpUrl = Field(description="API URL for organizations")
    repos_url: HttpUrl = Field(description="API URL for repositories")
    events_url: str = Field(description="API URL template for events")
    received_events_url: HttpUrl = Field(description="API URL for received events")
    type: UserType = Field(description="Type of user account")
    site_admin: bool = Field(description="Whether user is a GitHub site admin")
    name: str | None = Field(default=None, description="Full name")
    company: str | None = Field(default=None, description="Company affiliation")
    blog: str | None = Field(default=None, description="Blog URL")
    location: str | None = Field(default=None, description="Geographic location")
    email: str | None = Field(default=None, description="Public email address")
    hireable: bool | None = Field(default=None, description="Available for hire")
    bio: str | None = Field(default=None, description="User biography")
    twitter_username: str | None = Field(default=None, description="Twitter username")
    public_repos: int | None = Field(default=None, description="Number of public repos")
    public_gists: int | None = Field(default=None, description="Number of public gists")
    followers: int | None = Field(default=None, description="Number of followers")
    following: int | None = Field(default=None, description="Number of users following")
    created_at: datetime | None = Field(
        default=None, description="Account creation date"
    )
    updated_at: datetime | None = Field(default=None, description="Last profile update")


class GitHubLabel(BaseModel):
    """GitHub label model used in issues and pull requests"""

    id: int = Field(description="Unique label ID")
    node_id: str = Field(description="GraphQL node ID")
    url: HttpUrl = Field(description="API URL for label")
    name: str = Field(description="Label name")
    description: str | None = Field(default=None, description="Label description")
    color: str = Field(description="Label color (hex without #)")
    default: bool = Field(description="Whether this is a default label")


class GitHubMilestone(BaseModel):
    """GitHub milestone model used in issues and pull requests"""

    url: HttpUrl = Field(description="API URL for milestone")
    html_url: HttpUrl = Field(description="GitHub URL for milestone")
    labels_url: HttpUrl = Field(description="API URL for milestone labels")
    id: int = Field(description="Unique milestone ID")
    node_id: str = Field(description="GraphQL node ID")
    number: int = Field(description="Milestone number")
    state: str = Field(description="Milestone state", pattern="^(open|closed)$")
    title: str = Field(description="Milestone title")
    description: str | None = Field(default=None, description="Milestone description")
    creator: GitHubUser = Field(description="User who created the milestone")
    open_issues: int = Field(description="Number of open issues in milestone")
    closed_issues: int = Field(description="Number of closed issues in milestone")
    created_at: datetime = Field(description="Milestone creation date")
    updated_at: datetime = Field(description="Last milestone update")
    closed_at: datetime | None = Field(
        default=None, description="Milestone closure date"
    )
    due_on: datetime | None = Field(default=None, description="Milestone due date")


class GitHubBranch(BaseModel):
    """GitHub branch reference model"""

    label: str = Field(description="Branch label (e.g., 'user:branch-name')")
    ref: str = Field(description="Branch name")
    sha: str = Field(description="Commit SHA of branch head")
    user: GitHubUser | None = Field(default=None, description="Branch owner")
    repo: Repository | None = Field(
        default=None, description="Repository containing branch"
    )

    class Config:
        # Handle forward reference for Repository
        arbitrary_types_allowed = True
