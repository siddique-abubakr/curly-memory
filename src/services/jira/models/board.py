from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel

from .project import Project


class Board(BaseModel):
    id: int
    self: str
    name: str
    type: str
    location: Project
    is_private: bool = Field(alias="isPrivate")

    class Config:
        alias_generator = to_camel
        validate_by_name = True
