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
