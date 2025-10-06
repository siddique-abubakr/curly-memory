"""
GitHub commit models for the /commits endpoints.

These models represent commit data returned by GitHub's REST API.
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .base import GitHubUser


class VerificationReason(str, Enum):
    """Git signature verification reasons"""

    EXPIRED_KEY = "expired_key"
    NOT_SIGNING_KEY = "not_signing_key"
    GPGVERIFY_ERROR = "gpgverify_error"
    GPGVERIFY_UNAVAILABLE = "gpgverify_unavailable"
    UNSIGNED = "unsigned"
    UNKNOWN_SIGNATURE_TYPE = "unknown_signature_type"
    NO_USER = "no_user"
    UNVERIFIED_EMAIL = "unverified_email"
    BAD_EMAIL = "bad_email"
    UNKNOWN_KEY = "unknown_key"
    MALFORMED_SIGNATURE = "malformed_signature"
    INVALID = "invalid"
    VALID = "valid"
    BAD_CERT = "bad_cert"
    REVOKED_KEY = "revoked_key"


class CommitAuthor(BaseModel):
    """Git commit author/committer information"""

    name: str = Field(description="Author/committer name")
    email: str = Field(description="Author/committer email")
    date: datetime = Field(description="Commit date")


class GitTree(BaseModel):
    """Git tree reference"""

    url: HttpUrl = Field(description="API URL for tree")
    sha: str = Field(description="Tree SHA hash")


class CommitVerification(BaseModel):
    """Git commit signature verification"""

    verified: bool = Field(description="Whether the signature is verified")
    reason: VerificationReason = Field(description="Verification status reason")
    signature: str | None = Field(
        default=None, description="The signature that was extracted from the commit"
    )
    payload: str | None = Field(default=None, description="The value that was signed")
    verified_at: datetime | None = Field(
        default=None, description="When the signature was verified"
    )


class GitCommit(BaseModel):
    """Git commit data"""

    url: HttpUrl = Field(description="API URL for commit")
    author: CommitAuthor = Field(description="Commit author information")
    committer: CommitAuthor = Field(description="Commit committer information")
    message: str = Field(description="Commit message")
    tree: GitTree = Field(description="Git tree reference")
    comment_count: int = Field(description="Number of comments on commit")
    verification: CommitVerification = Field(
        description="Signature verification information"
    )


class CommitParent(BaseModel):
    """Parent commit reference"""

    url: HttpUrl = Field(description="API URL for parent commit")
    sha: str = Field(description="Parent commit SHA")
    html_url: HttpUrl | None = Field(
        default=None, description="GitHub URL for parent commit"
    )


class CommitStats(BaseModel):
    """Commit statistics (only available in single commit endpoint)"""

    additions: int = Field(description="Number of additions")
    deletions: int = Field(description="Number of deletions")
    total: int = Field(description="Total changes (additions + deletions)")


class CommitFile(BaseModel):
    """File changes in commit (only available in single commit endpoint)"""

    filename: str = Field(description="File name")
    additions: int = Field(description="Number of additions")
    deletions: int = Field(description="Number of deletions")
    changes: int = Field(description="Total changes")
    status: str = Field(
        description="Change status (added, removed, modified, renamed, copied)"
    )
    raw_url: HttpUrl = Field(description="Raw file URL")
    blob_url: HttpUrl = Field(description="Blob URL")
    patch: str | None = Field(default=None, description="Patch/diff for the file")
    sha: str | None = Field(default=None, description="File SHA")
    contents_url: HttpUrl | None = Field(
        default=None, description="API URL for file contents"
    )
    previous_filename: str | None = Field(
        default=None, description="Previous filename if renamed"
    )


class Commit(BaseModel):
    """GitHub commit model for API responses"""

    url: HttpUrl = Field(description="API URL for commit")
    sha: str = Field(description="Commit SHA hash")
    node_id: str = Field(description="GraphQL node ID")
    html_url: HttpUrl = Field(description="GitHub URL for commit")
    comments_url: HttpUrl = Field(description="API URL for commit comments")
    commit: GitCommit = Field(description="Git commit data")
    author: GitHubUser | None = Field(
        default=None, description="GitHub user who authored the commit"
    )
    committer: GitHubUser | None = Field(
        default=None, description="GitHub user who committed"
    )
    parents: list[CommitParent] = Field(description="Parent commits")


class CommitDetails(Commit):
    """Extended commit model with additional details (single commit endpoint)"""

    stats: CommitStats | None = Field(default=None, description="Commit statistics")
    files: list[CommitFile] | None = Field(
        default=None, description="Files changed in commit"
    )
