from core.logger import Logger
from .models import Board


class BoardService:
    """Service class for handling board-related operations."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()

    def get_boards_for_project(self, project: str) -> list[Board]:
        """Get all boards for a specific project."""
        try:
            boards = self.jira.boards(projectKeyOrID=project)
            self.logger.debug(f"Found {len(boards)} boards for project {project}")
            boards = [Board(**board.raw) for board in boards]
            return boards
        except Exception as e:
            self.logger.error(f"Error fetching boards for project {project}: {e}")
            return []

    def filter_scrum_boards(
        self, boards: list[Board], scrum_board_ids: list[int]
    ) -> list[Board]:
        """Filter boards to only include scrum boards."""
        scrum_boards = [board for board in boards if board.id in scrum_board_ids]
        self.logger.debug(f"Filtered to {len(scrum_boards)} scrum boards")
        return scrum_boards

    def get_board_info(self, board: Board) -> dict[str, any]:
        """Get formatted board information."""
        return board.model_dump()
