from jira.resources import Resource


class JiraChangelog(Resource):

    def __init__(self, options, session, raw=None):
        Resource.__init__(self, "issue/{0}/changelog/{1}", options, session)
        if raw:
            self._parse_raw(raw)
