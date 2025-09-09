"""
GitHub API parameter models for type safety and discoverability.
These models make it clear what parameters are available for each endpoint.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SortOrder(str, Enum):
    """Sort order options"""

    ASC = "asc"
    DESC = "desc"


class PullRequestState(str, Enum):
    """Pull request state options"""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class PullRequestSort(str, Enum):
    """Pull request sort options"""

    CREATED = "created"
    UPDATED = "updated"
    POPULARITY = "popularity"
    LONG_RUNNING = "long-running"


class IssueState(str, Enum):
    """Issue state options"""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class IssueSort(str, Enum):
    """Issue sort options"""

    CREATED = "created"
    UPDATED = "updated"
    COMMENTS = "comments"


class CommitParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/commits endpoint"""

    sha: Optional[str] = Field(
        default=None, description="SHA or branch to start listing commits from"
    )
    path: Optional[str] = Field(
        default=None,
        description="Only commits containing this file path will be returned",
    )
    author: Optional[str] = Field(
        default=None,
        description="GitHub username or email address to filter by commit author",
    )
    committer: Optional[str] = Field(
        default=None,
        description="GitHub username or email address to filter by commit committer",
    )
    since: Optional[str] = Field(
        default=None,
        description="Only show results that were last updated after the given time"
        "(ISO 8601: YYYY-MM-DDTHH:MM:SSZ)",
    )
    until: Optional[str] = Field(
        default=None,
        description="Only commits before this date will be returned"
        "(ISO 8601: YYYY-MM-DDTHH:MM:SSZ)",
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    @field_validator("since", "until")
    def validate_date_format(cls, v):
        if v and not v.endswith("Z"):
            try:
                # Try to parse and reformat to ensure ISO 8601
                dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                return dt.isoformat().replace("+00:00", "Z")
            except ValueError:
                raise ValueError(
                    "Date must be in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ"
                )
        return v

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "since": "2024-01-01T00:00:00Z",
                "until": "2024-12-31T23:59:59Z",
                "author": "username",
                "per_page": 50,
                "page": 1,
            }
        }


class PullRequestParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/pulls endpoint"""

    state: Optional[PullRequestState] = Field(
        default=PullRequestState.OPEN, description="State of pull requests to retrieve"
    )
    head: Optional[str] = Field(
        default=None,
        description="Filter pulls by head user or head organization and branch name"
        "(format: user:ref-name)",
    )
    base: Optional[str] = Field(
        default=None, description="Filter pulls by base branch name"
    )
    sort: Optional[PullRequestSort] = Field(
        default=PullRequestSort.CREATED, description="What to sort results by"
    )
    direction: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort direction"
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": 1,
            }
        }


class IssueParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/issues endpoint"""

    milestone: Optional[str] = Field(
        default=None, description="Milestone number or 'none' or '*'"
    )
    state: Optional[IssueState] = Field(
        default=IssueState.OPEN, description="State of issues to retrieve"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Username assigned to the issues or 'none' for unassigned",
    )
    creator: Optional[str] = Field(
        default=None, description="Username that created the issues"
    )
    mentioned: Optional[str] = Field(
        default=None, description="Username that's mentioned in the issues"
    )
    labels: Optional[str] = Field(
        default=None,
        description="Comma-separated list of label names (e.g., 'bug,help wanted')",
    )
    sort: Optional[IssueSort] = Field(
        default=IssueSort.CREATED, description="What to sort results by"
    )
    direction: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort direction"
    )
    since: Optional[str] = Field(
        default=None,
        description="Only show issues updated after this date"
        "(ISO 8601: YYYY-MM-DDTHH:MM:SSZ)",
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "state": "all",
                "labels": "bug,enhancement",
                "sort": "updated",
                "direction": "desc",
                "per_page": 50,
            }
        }


class ContributorParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/contributors endpoint"""

    anon: Optional[bool] = Field(
        default=False, description="Include anonymous contributors in results"
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        schema_extra = {"example": {"anon": True, "per_page": 100, "page": 1}}


class BranchParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/branches endpoint"""

    protected: Optional[bool] = Field(
        default=None,
        description="Only show protected branches if True, only unprotected if False",
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        schema_extra = {"example": {"protected": True, "per_page": 50, "page": 1}}


class ReleaseParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/releases endpoint"""

    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        schema_extra = {"example": {"per_page": 100, "page": 1}}


class PullRequestCommitsParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/pulls/{number}/commits endpoint"""

    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        schema_extra = {"example": {"per_page": 100, "page": 1}}


class PullRequestReviewsParams(BaseModel):
    """Parameters for /repos/{owner}/{repo}/pulls/{number}/reviews endpoint"""

    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Number of results per page (1-100)"
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number of results to fetch"
    )

    class Config:
        schema_extra = {"example": {"per_page": 50, "page": 1}}
