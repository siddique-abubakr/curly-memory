from pydantic import BaseModel, Field
from .avatar import AvatarUrls


class User(BaseModel):
    """User information (assignee, reporter, creator, etc.)"""

    self: str
    account_id: str = Field(alias="accountId")
    email_address: str | None = Field(alias="emailAddress", default=None)
    avatar_urls: AvatarUrls = Field(alias="avatarUrls")
    display_name: str = Field(alias="displayName")
    active: bool
    time_zone: str = Field(alias="timeZone")
    account_type: str = Field(alias="accountType")
