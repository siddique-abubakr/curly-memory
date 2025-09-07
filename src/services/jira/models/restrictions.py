from pydantic import BaseModel, Field


class IssueRestriction(BaseModel):
    """Issue restrictions"""

    issue_restrictions: dict[str, object] = Field(alias="issuerestrictions")
    should_display: bool = Field(alias="shouldDisplay")