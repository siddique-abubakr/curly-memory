from pydantic import BaseModel, Field


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