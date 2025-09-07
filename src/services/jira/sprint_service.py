from datetime import datetime, timezone

from core.logger import Logger
from .models import Sprint


class SprintService:
    """Service class for handling sprint-related operations."""

    def __init__(self, jira_client):
        self.jira = jira_client
        self.logger = Logger.get_logger()

    def get_sprints_for_board(
        self, board_id: int, filter_config: dict[str, any] = None
    ) -> list[Sprint]:
        """Get sprints for a given board based on filter configuration."""
        try:
            # Get all sprints for the board using pagination
            all_sprints = []
            start_at = 0
            max_results = 50  # Keep reasonable page size

            while True:
                sprints_page = self.jira.sprints(
                    board_id=board_id, startAt=start_at, maxResults=max_results
                )

                if not sprints_page:
                    break

                all_sprints.extend(sprints_page)
                start_at += max_results

                # If we got fewer results than max_results, we've reached the end
                if len(sprints_page) < max_results:
                    break

            self.logger.debug(
                f"Found {len(all_sprints)} total sprints for board {board_id}"
            )

            all_sprints = [Sprint(**sprint.raw) for sprint in all_sprints]

            if not filter_config:
                return all_sprints

            # Apply filters
            filtered_sprints = self._apply_sprint_filters(all_sprints, filter_config)
            self.logger.debug(
                f"Filtered to {len(filtered_sprints)} sprints for board {board_id}"
            )

            return filtered_sprints

        except Exception as e:
            self.logger.error(f"Error fetching sprints for board {board_id}: {e}")
            return []

    def _apply_sprint_filters(
        self, sprints: list[Sprint], filter_config: dict[str, any]
    ) -> list[Sprint]:
        """Apply various filters to sprints."""
        filtered_sprints = []

        for sprint in sprints:
            if self._sprint_matches_filters(sprint, filter_config):
                filtered_sprints.append(sprint)

        return filtered_sprints

    def _sprint_matches_filters(
        self, sprint: Sprint, filter_config: dict[str, any]
    ) -> bool:
        """Check if a sprint matches the filter criteria."""
        try:
            # Check specific sprint IDs first
            if filter_config.get("specific_sprint_ids"):
                if sprint.id in filter_config["specific_sprint_ids"]:
                    return True
                else:
                    return False

            # Check date range filter
            if filter_config.get("date_range", {}).get("enabled", False):
                date_range = filter_config["date_range"]
                start_date = date_range.get("start_date")
                end_date = date_range.get("end_date")

                if not self._sprint_in_date_range(
                    sprint, start_date, end_date, filter_config
                ):
                    return False

            # Check sprint state filter
            if filter_config.get("sprint_states"):
                if not self._sprint_matches_state(
                    sprint, filter_config["sprint_states"]
                ):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking sprint filters: {e}")
            return False

    def _sprint_in_date_range(
        self,
        sprint: Sprint,
        start_date: datetime,
        end_date: datetime,
        filter_config: dict[str, any],
    ) -> bool:
        """Check if sprint falls within the specified date range."""
        try:
            # Handle sprints with no end date
            if not hasattr(sprint, "endDate") or not sprint.endDate:
                return filter_config.get("include_no_end_date", False)

            sprint_start = datetime.fromisoformat(sprint.startDate)
            sprint_end = datetime.fromisoformat(sprint.endDate)

            # Check if sprint overlaps with the date range
            # Sprint is included if it overlaps with the date range
            # (starts before the end date AND ends after the start date)
            overlaps = sprint_start <= end_date and sprint_end >= start_date
            return overlaps

        except Exception as e:
            self.logger.error(f"Error checking sprint date range: {e}")
            return False

    def _sprint_matches_state(self, sprint: Sprint, allowed_states: list[str]) -> bool:
        """Check if sprint state matches allowed states."""
        try:
            sprint_state = getattr(sprint, "state", "unknown").lower()
            return sprint_state in [state.lower() for state in allowed_states]
        except Exception as e:
            self.logger.error(f"Error checking sprint state: {e}")
            return False

    def get_active_sprints(self, board_id: int) -> list[any]:
        """Get active sprints for a given board (legacy method)."""
        return self.get_sprints_for_board(board_id, {"sprint_states": ["active"]})

    def is_sprint_active(self, sprint: Sprint) -> bool:
        """Check if a sprint is currently active."""
        try:
            start_date = datetime.fromisoformat(sprint.startDate)
            end_date = datetime.fromisoformat(sprint.endDate)
            current_time = datetime.now(timezone.utc)

            is_active = start_date < current_time < end_date
            status = "active" if is_active else "not active"
            self.logger.debug(f"Sprint {sprint.name} (ID: {sprint.id}) is {status}")
            return is_active
        except Exception as e:
            self.logger.error(f"Error checking sprint status: {e}")
            return False

    def get_sprint_info(self, sprint: Sprint) -> dict[str, any]:
        """Get formatted sprint information."""
        try:
            self.logger.debug(f"Sprint details: {sprint}")

            return sprint.model_dump()
        except Exception as e:
            self.logger.error(f"Error getting sprint info: {e}")
            return {}
