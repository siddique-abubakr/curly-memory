"""
GitHub contributor and branch models for various endpoints.

These models represent contributor and branch data returned by GitHub's REST API.
"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class Contributor(BaseModel):
    """GitHub repository contributor model"""

    login: str = Field(description="Username")
    id: int = Field(description="Unique user ID")
    node_id: str = Field(description="GraphQL node ID")
    avatar_url: HttpUrl = Field(description="User's avatar image URL")
    gravatar_id: Optional[str] = Field(default=None, description="Gravatar ID")
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
    type: str = Field(description="User type")
    site_admin: bool = Field(description="Whether user is a GitHub site admin")
    contributions: int = Field(description="Number of contributions to repository")


class BranchProtection(BaseModel):
    """Branch protection settings"""

    enabled: bool = Field(description="Whether branch protection is enabled")
    required_status_checks: Optional[dict] = Field(
        default=None, description="Required status checks"
    )


class BranchCommit(BaseModel):
    """Branch commit reference"""

    sha: str = Field(description="Commit SHA")
    url: HttpUrl = Field(description="API URL for commit")


class Branch(BaseModel):
    """GitHub repository branch model"""

    name: str = Field(description="Branch name")
    commit: BranchCommit = Field(description="Latest commit on branch")
    protected: bool = Field(description="Whether branch is protected")
    protection: Optional[BranchProtection] = Field(
        default=None, description="Branch protection settings"
    )
    protection_url: Optional[HttpUrl] = Field(
        default=None, description="API URL for protection settings"
    )
