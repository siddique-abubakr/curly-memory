from clients.jira import jira
from clients import github
from core.constants import (
    PROJECTS_TO_INCLUDE,
    SCRUM_BOARDS,
    ALL_BOARDS,
    SPRINT_FILTER_CONFIG,
    GITHUB_CONFIG
)
from core.logger import Logger
from dotenv import load_dotenv
from services import (
    JiraAnalyzer,
    GitHubAnalyzer
)

# Load the environment variables
load_dotenv()


def main():
    """Main application entry point."""
    logger = Logger.get_logger(name=__name__)
    logger.info("Starting the Jira analysis application")

    try:
        # Initialize the analyzers
        jira_analyzer = JiraAnalyzer(jira)
        # github_analyzer = GitHubAnalyzer(github)

        # Pre-fetch Kanban issues from ALL Kanban boards/projects
        # This allows us to integrate them into Scrum sprint analysis
        logger.info("Pre-fetching Kanban issues from all Kanban boards...")
        all_kanban_issues = []

        from core.constants import KANBAN_BOARDS
        from core.enums import Projects

        # Fetch Kanban issues from project 10006 (LITMUSTEST_KANBAN)
        for project_id in [Projects.LITMUSTEST_KANBAN.value]:
            for board_id in KANBAN_BOARDS:
                try:
                    date_filter = SPRINT_FILTER_CONFIG.get("date_range")
                    kanban_issues = jira_analyzer.issue_service.get_all_issues_for_board(
                        project_id, board_id, date_filter
                    )
                    logger.info(
                        f"Fetched {len(kanban_issues)} Kanban issues from "
                        f"project {project_id}, board {board_id}"
                    )
                    all_kanban_issues.extend(kanban_issues)
                except Exception as e:
                    logger.error(f"Error fetching Kanban issues from board {board_id}: {e}")

        logger.info(f"Total Kanban issues fetched: {len(all_kanban_issues)}")

        # Analyze each project
        for project in PROJECTS_TO_INCLUDE:
            logger.info(f"Processing project: {project}")

            # status_results = jira_analyzer.analyze_status_metrics_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )

            # status_report = jira_analyzer.generate_status_report(status_results)
            # logger.info(f"\n{status_report}")

            # Option 3: WIP Limit Violations only (uncomment to use)
            wip_results = jira_analyzer.analyze_wip_violations_only(
                project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            )
            wip_report = jira_analyzer.generate_wip_violations_report(wip_results)
            logger.info(f"\n{wip_report}")

            # Option 4: Prod Bug Analysis only (uncomment to use)
            # prod_bug_results = jira_analyzer.analyze_prod_bugs_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # # Standard prod bug report
            # prod_bug_report = jira_analyzer.generate_prod_bugs_report(
            #   prod_bug_results
            # )
            # logger.info(f"\n{prod_bug_report}")

            # Quarterly prod bug report
            # quarterly_report = analyzer.generate_prod_bugs_quarterly_report(
            #   prod_bug_results
            # )
            # logger.info(f"\n{quarterly_report}")

            # Option 5: Cycle Time Analysis (integrates Scrum and Kanban issues)
            # cycle_time_results = jira_analyzer.analyze_cycle_time_only(
            #     project, ALL_BOARDS, SPRINT_FILTER_CONFIG, "sprint_wise", all_kanban_issues
            # )
            # cycle_time_report = jira_analyzer.generate_cycle_time_report(
            #     cycle_time_results
            # )
            # logger.info(f"\n{cycle_time_report}")

        # Option 6: GitHub PR Analysis (uncomment to use)
        # github_results = github_analyzer.analyze_repository_prs(GITHUB_CONFIG)
        # github_report = github_analyzer.generate_github_report(github_results)
        # logger.info(f"\n{github_report}")

        # Optional: Detailed GitHub report
        # github_detailed = github_analyzer.generate_github_detailed_report(
        #   github_results
        # )
        # logger.info(f"\n{github_detailed}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
