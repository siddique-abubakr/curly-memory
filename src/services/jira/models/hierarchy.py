from pydantic import BaseModel, Field

from .metadata import Priority, IssueType
from .status import Status


class SubtaskFields(BaseModel):
    """Fields for subtask issues"""

    summary: str
    status: Status
    priority: Priority
    issue_type: IssueType = Field(alias="issuetype")


class Subtask(BaseModel):
    """Subtask information"""

    id: str
    key: str
    self: str
    fields: SubtaskFields


class ParentFields(BaseModel):
    """Fields for parent issue"""

    summary: str
    status: Status
    priority: Priority
    issue_type: IssueType = Field(alias="issuetype")


class Parent(BaseModel):
    """Parent issue information"""

    id: str
    key: str
    self: str
    fields: ParentFields