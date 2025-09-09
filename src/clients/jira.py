import os

from services.jira.extensions.jira_extended import JiraEx


class JiraClient:
    """
    JiraClient is a singleton class that provides a JIRA API client.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(JiraClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, server=None, email=None, api_token=None):
        if not hasattr(self, "jira"):
            self.jira = JiraEx(
                server=server or os.getenv("JIRA_SERVER"),
                basic_auth=(
                    email or os.getenv("JIRA_EMAIL"),
                    api_token or os.getenv("JIRA_API_TOKEN"),
                ),
            )


# Export the JiraClient instance as a global variable
client = JiraClient()
jira = client.jira
