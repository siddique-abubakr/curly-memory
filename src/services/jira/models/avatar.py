from pydantic import BaseModel, Field


class AvatarUrls(BaseModel):
    """Avatar URLs for users and projects"""

    size_48x48: str = Field(alias="48x48")
    size_24x24: str = Field(alias="24x24")
    size_16x16: str = Field(alias="16x16")
    size_32x32: str = Field(alias="32x32")
