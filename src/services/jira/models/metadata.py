from pydantic import BaseModel, Field


class Priority(BaseModel):
    """Issue priority information"""

    self: str
    icon_url: str = Field(alias="iconUrl")
    name: str
    id: str


class IssueType(BaseModel):
    """Issue type information"""

    self: str
    id: str
    description: str
    icon_url: str = Field(alias="iconUrl")
    name: str
    subtask: bool
    avatar_id: int = Field(alias="avatarId")
    entity_id: str = Field(alias="entityId")
    hierarchy_level: int = Field(alias="hierarchyLevel")


class Resolution(BaseModel):
    """Issue resolution information"""

    self: str
    id: str
    description: str
    name: str
