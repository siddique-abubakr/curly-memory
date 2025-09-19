from clients.jira import jira
from core.constants import PROJECTS_TO_INCLUDE, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
from core.logger import Logger
from dotenv import load_dotenv
from services import JiraAnalyzer

# Load the environment variables
load_dotenv()


def main():
    """Main application entry point."""
    logger = Logger.get_logger(name=__name__)
    logger.info("Starting the Jira analysis application")

    try:
        # Initialize the analyzer
        analyzer = JiraAnalyzer(jira)

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
            # resolution_results = analyzer.analyze_resolution_metrics_only(
            #     project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            # )
            # resolution_report = analyzer.generate_resolution_report(resolution_results)
            # logger.info(f"\n{resolution_report}")

            # # Status metrics only
            status_results = analyzer.analyze_status_metrics_only(
                project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            )
            status_report = analyzer.generate_status_report(status_results)
            logger.info(f"\n{status_report}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
