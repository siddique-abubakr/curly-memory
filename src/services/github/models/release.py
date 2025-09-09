"""
GitHub release models for the /releases endpoints.

These models represent release data returned by GitHub's REST API.
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .base import GitHubUser


class ReleaseAssetState(str, Enum):
    """Release asset states"""

    UPLOADED = "uploaded"
    OPEN = "open"


class ReleaseAuthor(GitHubUser):
    """Release author (extends GitHubUser)"""

    pass


class ReleaseAsset(BaseModel):
    """GitHub release asset model"""

    url: HttpUrl = Field(description="API URL for asset")
    browser_download_url: HttpUrl = Field(description="Direct download URL")
    id: int = Field(description="Asset ID")
    node_id: str = Field(description="GraphQL node ID")
    name: str = Field(description="Asset filename")
    label: str | None = Field(default=None, description="Asset label/description")
    state: ReleaseAssetState = Field(description="Asset state")
    content_type: str = Field(description="MIME content type")
    size: int = Field(description="Asset size in bytes")
    download_count: int = Field(description="Number of downloads")
    created_at: datetime = Field(description="Asset creation date")
    updated_at: datetime = Field(description="Last asset update")
    uploader: ReleaseAuthor = Field(description="User who uploaded the asset")


class ReleaseReactions(BaseModel):
    """Release reaction counts"""

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


class Release(BaseModel):
    """GitHub release model for API responses"""

    url: HttpUrl = Field(description="API URL for release")
    html_url: HttpUrl = Field(description="GitHub URL for release")
    assets_url: HttpUrl = Field(description="API URL for release assets")
    upload_url: str = Field(description="URL template for uploading assets")
    tarball_url: HttpUrl | None = Field(
        default=None, description="Tarball download URL"
    )
    zipball_url: HttpUrl | None = Field(
        default=None, description="Zipball download URL"
    )
    id: int = Field(description="Release ID")
    node_id: str = Field(description="GraphQL node ID")
    tag_name: str = Field(description="Git tag name")
    target_commitish: str = Field(description="Target branch or commit")
    name: str | None = Field(default=None, description="Release name/title")
    body: str | None = Field(default=None, description="Release description/notes")
    draft: bool = Field(description="Whether release is a draft")
    prerelease: bool = Field(description="Whether release is a prerelease")
    created_at: datetime = Field(description="Release creation date")
    published_at: datetime | None = Field(
        default=None, description="Release publication date"
    )
    author: ReleaseAuthor = Field(description="User who created the release")
    assets: list[ReleaseAsset] = Field(description="Release assets")
    body_html: str | None = Field(
        default=None, description="Release body rendered as HTML"
    )
    body_text: str | None = Field(
        default=None, description="Release body as plain text"
    )
    mentions_count: int | None = Field(
        default=None, description="Number of user mentions"
    )
    discussion_url: HttpUrl | None = Field(
        default=None, description="Discussion URL if enabled"
    )
    reactions: ReleaseReactions | None = Field(
        default=None, description="Release reactions"
    )
