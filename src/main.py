from clients.jira import jira
from clients import github
from core.constants import (
    PROJECTS_TO_INCLUDE,
    SCRUM_BOARDS,
    SPRINT_FILTER_CONFIG,
    GITHUB_CONFIG
)
from core.logger import Logger
from dotenv import load_dotenv
from services import JiraAnalyzer, GitHubAnalyzer

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

        # Analyze each project
        for project in PROJECTS_TO_INCLUDE:
            logger.info(f"Processing project: {project}")

            # Option 1: Combined analysis (default behavior)
            # results = analyzer.analyze_project(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # report = analyzer.generate_report(results)
            # logger.info(f"\n{report}")

            # Option 2: Separate reports (uncomment to use)
            # Resolution metrics only
            # resolution_results = jira_analyzer.analyze_resolution_metrics_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # resolution_report = jira_analyzer.generate_resolution_report(
            #   resolution_results
            # )
            # logger.info(f"\n{resolution_report}")

            # # Status metrics only
            # status_results = analyzer.analyze_status_metrics_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # status_report = analyzer.generate_status_report(status_results)
            # logger.info(f"\n{status_report}")

            # Option 3: WIP Limit Violations only (uncomment to use)
            # wip_results = jira_analyzer.analyze_wip_violations_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # wip_report = jira_analyzer.generate_wip_violations_report(wip_results)
            # logger.info(f"\n{wip_report}")

            # Option 4: Prod Bug Analysis only (uncomment to use)
            prod_bug_results = jira_analyzer.analyze_prod_bugs_only(
                project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            )
            # Standard prod bug report
            prod_bug_report = jira_analyzer.generate_prod_bugs_report(prod_bug_results)
            logger.info(f"\n{prod_bug_report}")

            # Quarterly prod bug report
            # quarterly_report = analyzer.generate_prod_bugs_quarterly_report(prod_bug_results)
            # logger.info(f"\n{quarterly_report}")

        # Option 5: GitHub PR Analysis (uncomment to use)
        # github_results = github_analyzer.analyze_repository_prs(GITHUB_CONFIG)
        # github_report = github_analyzer.generate_github_report(github_results)
        # logger.info(f"\n{github_report}")

        # Optional: Detailed GitHub report
        # github_detailed = github_analyzer.generate_github_detailed_report(github_results)
        # logger.info(f"\n{github_detailed}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
