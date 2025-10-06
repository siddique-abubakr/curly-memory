import os
from dotenv import load_dotenv
from core.enums import Boards, Projects
from datetime import datetime, timezone

load_dotenv()

PROJECTS_TO_INCLUDE = [Projects.LITMUSTEST.value, Projects.LITMUSTEST_KANBAN.value]
SCRUM_BOARDS = [Boards.LT.value]
KANBAN_BOARDS = [Boards.LTK_BOARD.value]
ALL_BOARDS = SCRUM_BOARDS + KANBAN_BOARDS

# Sprint filtering configurations
SPRINT_FILTER_CONFIG = {
    # Date range filtering (since April 2025)
    "date_range": {
        "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc),  # March 1, 2025
        "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc),  # Current date
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

# Github Configurations
GITHUB_CONFIG = {
    "owner": "arbisoft",
    "repos": [
        "litmustest-backend",
        "Litmustest",
        "edx-ora2-1",
        "obvious"
    ],
    "headers": {
        "Authorization": f"token {os.getenv("GITHUB_TOKEN")}",
        "Accept": "application/vnd.github+json",
    },
    # Configuration: Choose grouping method
    "grouping": "monthly",  # Options: "monthly", "semi-monthly"

    # PRIMARY FILTER: Date filtering (business logic)
    "start_date": "2025-04-01",  # Format: YYYY-MM-DD, set to None to disable
    "end_date": None,  # Format: YYYY-MM-DD, set to None to disable

    # SECONDARY FILTER: Performance optimization (applied after date filter)
    # Use this to limit analysis to most recent N PRs for faster testing/development
    # Set to None to analyze all PRs that pass the date filter
    "max_prs_per_repo": None,  # Limit PRs per repository for faster analysis
}
