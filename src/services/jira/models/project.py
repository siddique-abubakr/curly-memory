from pydantic import BaseModel, Field, AliasChoices
from pydantic.alias_generators import to_camel

from .avatar import AvatarUrls


class Project(BaseModel):
    """Project information"""

    name: str
    project_id: int | None = Field(alias="projectId", default=None)
    project_type_key: str | None = Field(alias="projectTypeKey", default=None)
    avatar_uri: str | None = Field(alias="avatarURI", default=None)
    simplified: bool = Field(default=False)
    display_name: str | None = Field(alias="displayName", default=None)
    avatar_urls: AvatarUrls | None = Field(alias="avatarUrls", default=None)
    project_name: str = Field(validation_alias=AliasChoices("projectName", "name"))
    project_key: str = Field(validation_alias=AliasChoices("projectKey", "key"))

    class Config:
        alias_generator = to_camel
        validate_by_name = True
