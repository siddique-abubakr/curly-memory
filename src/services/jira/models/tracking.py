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
    field_id: str
    from_id: str = Field(alias="from")
    from_string: str
    to_id: str = Field(alias="to")
    to_string: str


class Changelog(BaseModel):
    "Ticket history"

    id: str
    author: User
    created: str
    items: list[ChangelogItem]
