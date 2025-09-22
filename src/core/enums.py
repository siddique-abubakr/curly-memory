from enum import Enum


class Boards(Enum):
    """
    Jira Board IDs
    """

    LT = 2
    LTK_BOARD = 6


class Projects(Enum):
    """
    Jira Project IDs
    """

    LITMUSTEST = "10001"
    LITMUSTEST_KANBAN = "10006"


class Status(Enum):
    """
    Jira ticket status for Litmustest
    """

    TODO = "10009"
    IN_PROGRESS = "10010"
    REVIEW_AND_TESTING = "10017"
    BLOCKED = "10012"
    QA_REVIEW = "10020"
    DONE = "10013"


class CustomField(Enum):
    SPRINT = "customfield_10020"
    WIP_LABELS = "customfield_10043"


class WIPLabels(Enum):
    TODO_LIMIT_EXCEEDED = "TodoLimitExceeded"
    INPROGRESS_LIMIT_EXCEEDED = "InProgressLimitExceeded"
    REVIEWANDTESTING_LIMIT_EXCEEDED = "ReviewAndTestingLimitExceeded"
    BLOCKED_LIMIT_EXCEEDED = "BlockedLimitExceeded"
    QAREVIEW_LIMIT_EXCEEDED = "QaReviewLimitExceeded"
