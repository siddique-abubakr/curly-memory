from pydantic import BaseModel, Field


class StatusCategory(BaseModel):
    """Status category information"""

    self: str
    id: int
    key: str
    color_name: str = Field(alias="colorName")
    name: str


class Status(BaseModel):
    """Issue status information"""

    self: str
    description: str
    icon_url: str = Field(alias="iconUrl")
    name: str
    id: str
    status_category: StatusCategory = Field(alias="statusCategory")
