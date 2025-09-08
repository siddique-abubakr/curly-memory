from pydantic import BaseModel, Field
from services.jira.models.user import User


class Watches(BaseModel):
    """Issue watchers information"""

    self: str
    watch_count: int = Field(alias="watchCount")
    is_watching: bool = Field(alias="isWatching")


class Votes(BaseModel):
    """Issue votes information"""

    self: str
    votes: int
    has_voted: bool = Field(alias="hasVoted")


class Progress(BaseModel):
    """Progress tracking"""

    progress: int
    total: int


class ChangelogItem(BaseModel):
    "Changelog Item"

    field: str
    fieldtype: str
    field_id: str | None = Field(alias="fieldId", default=None)
    from_id: str | None = Field(alias="from", default=None)
    from_string: str | None = Field(alias="fromString", default=None)
    to_id: str | None = Field(alias="to", default=None)
    to_string: str | None = Field(alias="toString", default=None)


class Changelog(BaseModel):
    "Ticket history"

    id: str
    author: User
    created: str
    items: list[ChangelogItem]
