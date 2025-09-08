from jira import JIRA
from jira.client import ResultList

from .changelog import JiraChangelog


# add changelogs function that loads all the changelogs using paging
# if the original JIRA class ever adds this method
# then I could switch to using it instead
class JiraEx(JIRA):

    def changelogs(self, issue_key) -> ResultList[JiraChangelog]:
        return self._fetch_pages(
            JiraChangelog, "values", "issue/%s/changelog" % issue_key, maxResults=False
        )
