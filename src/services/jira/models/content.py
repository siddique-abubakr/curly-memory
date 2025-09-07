from pydantic import BaseModel, Field

from .user import User


class Attachment(BaseModel):
    """Issue attachment information"""

    self: str
    id: str
    filename: str
    author: User
    created: str
    size: int
    mime_type: str = Field(alias="mimeType")
    content: str
    thumbnail: str | None = None


class Comment(BaseModel):
    """Issue comment information"""

    self: str
    id: str
    author: User
    body: str
    update_author: User = Field(alias="updateAuthor")
    created: str
    updated: str
    jsd_public: bool = Field(alias="jsdPublic")


class Comments(BaseModel):
    """Comments collection"""

    comments: list[Comment]
    self: str
    max_results: int = Field(alias="maxResults")
    total: int
    start_at: int = Field(alias="startAt")


class Worklog(BaseModel):
    """Worklog collection (usually empty)"""

    start_at: int = Field(alias="startAt")
    max_results: int = Field(alias="maxResults")
    total: int
    worklogs: list[dict]  # Usually empty, could be more specific if needed
