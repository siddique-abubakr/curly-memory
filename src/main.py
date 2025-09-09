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

            # Analyze the project with sprint filter configuration
            results = analyzer.analyze_project(
                project, SCRUM_BOARDS, SPRINT_FILTER_CONFIG
            )

            # Generate and log the report
            report = analyzer.generate_report(results)
            logger.info(f"\n{report}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
