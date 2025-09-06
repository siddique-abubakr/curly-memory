from core.enums import Boards, Projects
from datetime import datetime, timezone

PROJECTS_TO_INCLUDE = [Projects.LITMUSTEST.value, Projects.LITMUSTEST_KANBAN.value]
SCRUM_BOARDS = [Boards.LT.value]
KANBAN_BOARDS = [Boards.LTK_BOARD.value]

# Sprint filtering configurations
SPRINT_FILTER_CONFIG = {
    # Date range filtering (since April 2025)
    "date_range": {
        "start_date": datetime(2025, 7, 1, tzinfo=timezone.utc),  # July 1, 2025
        "end_date": datetime.now(timezone.utc),  # Current date
        "enabled": True,
    },
    # Sprint state filtering
    "sprint_states": [
        "active",
        "closed",
        # "future"
    ],  # All states
    # Specific sprint IDs (optional - leave empty to use date range)
    "specific_sprint_ids": [],
    # Whether to include sprints with no end date
    "include_no_end_date": True,
}
