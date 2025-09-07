from datetime import datetime, timedelta
from pydantic import BaseModel, Field, computed_field

from .project import Project
from .status import Status, StatusCategory
from .user import User
from .sprint import Sprint
from .metadata import Priority, IssueType, Resolution
from .content import Attachment, Comments, Worklog
from .tracking import Watches, Votes, Progress
from .restrictions import IssueRestriction
from .hierarchy import Subtask, Parent


class IssueFields(BaseModel):
    """All issue fields"""

    # Basic issue info
    statuscategorychangedate: str
    issue_type: IssueType = Field(alias="issuetype")
    parent: Parent | None = None
    timespent: int | None = None
    project: Project
    fix_versions: list[object] = Field(alias="fixVersions")
    aggregate_timespent: int | None = Field(alias="aggregatetimespent")
    status_category: StatusCategory = Field(alias="statusCategory")
    resolution: Resolution | None = None
    resolution_date: str | None = Field(alias="resolutiondate")
    work_ratio: int = Field(alias="workratio")
    issue_restriction: IssueRestriction = Field(alias="issuerestriction")
    watches: Watches
    last_viewed: str | None = Field(alias="lastViewed")
    created: str
    updated: str
    status: Status
    components: list[object]
    time_original_estimate: int | None = Field(alias="timeoriginalestimate")
    description: str | None = None
    time_tracking: dict[str, object] = Field(alias="timetracking")
    security: object | None = None
    attachment: list[Attachment]
    aggregate_time_estimate: int | None = Field(alias="aggregatetimeestimate")
    summary: str
    creator: User
    subtasks: list[Subtask]
    reporter: User
    aggregate_progress: Progress = Field(alias="aggregateprogress")
    environment: str | None = None
    due_date: str | None = Field(alias="duedate")
    progress: Progress
    votes: Votes
    comment: Comments
    worklog: Worklog

    # People
    assignee: User | None = None
    priority: Priority
    labels: list[str]
    versions: list[object]
    issue_links: list[object] = Field(alias="issuelinks")
    time_estimate: int | None = Field(alias="timeestimate")
    aggregate_time_original_estimate: int | None = Field(
        alias="aggregatetimeoriginalestimate"
    )

    # Custom fields
    customfield_10029: object | None = None
    customfield_10109: object | None = None
    customfield_10020: list[Sprint] | None = None  # Sprints
    customfield_10021: object | None = None
    customfield_10016: float | None = None  # Story points
    customfield_10019: str | None = None  # Rank
    customfield_10175: object | None = None
    customfield_10043: list[str] | None = None  # Labels like "InProgressLimitExceeded"
    customfield_10000: str | None = None
    customfield_10039: object | None = None


class Issue(BaseModel):
    """Main issue model"""

    expand: str
    id: str
    self: str
    key: str
    fields: IssueFields

    class Config:
        # Allow population by field name and alias
        validate_by_name = True

    @computed_field
    def resolution_time(self) -> timedelta:
        created = datetime.fromisoformat(self.fields.created)
        updated = datetime.fromisoformat(self.fields.updated)

        return updated - created

    @computed_field
    def resolution_time_days(self) -> timedelta:
        return self.resolution_time.days
