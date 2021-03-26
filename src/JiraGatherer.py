import itertools
from jira import JIRA, JIRAError
from constants import TOKEN_AUTH, USER_AUTH
from gatherer import Gatherer

# By default, the client will connect to a Jira instance started from the Atlassian Plugin SDK
# (see https://developer.atlassian.com/display/DOCS/Installing+the+Atlassian+Plugin+SDK for details).
# Override this with the options parameter.
# Licenses https://my.atlassian.com/products/index?sen=16469943&evalId=16469943&eval=true#license_16469943


class JiraGatherer(Gatherer):
    def __init__(self, url, credentials):
        options = {"server": url}
        if USER_AUTH in credentials:
            credentials[USER_AUTH] = (credentials[USER_AUTH][0],
                                      credentials[USER_AUTH][1])
            self.jira = JIRA(options, auth=credentials[USER_AUTH])

    def parse_response(self, request_type, response):
        return response

    def send_request(self):
        # Get all projects viewable by anonymous users.
        projects = self.jira.projects()
        # Sort available project keys, then return the second, third, and fourth keys.
        issues = []
        for project in projects:
            key = project.key
            for index in itertools.count(1):
                try:
                    # Get an issue.
                    issue = self.jira.issue(key + "-" + str(index))
                    issues.append(issue)
                except JIRAError:
                    # Last issue found was previous iteration
                    break
                # Find all comments made by Atlassians on this issue.
                atl_comments = [
                    comment
                    for comment in issue.fields.comment.comments
                    # if re.search(r"@atlassian.com$", comment.author.emailAddress)
                ]
                print(issue.fields.created, issue.fields.creator)
                print(issue.fields.summary)
                print(issue.fields.description)
                print(issue.fields.issuetype)
                print(issue.fields.priority)
                if issue.fields.reporter:
                    print("Reporter: " + issue.fields.reporter.name)
                if issue.fields.assignee:
                    print("Assignee: " + issue.fields.assignee.name)
                for comment in atl_comments:
                    print(comment)
                # # Change the issue's summary and description.
                # issue.update(
                #     summary="I'm different!", description="Changed the summary to be different."
                # )
        # # Change the issue without sending updates
        # issue.update(notify=False, description="Quiet summary update.")
        #
        # # You can update the entire labels field like this
        # issue.update(fields={"labels": ["AAA", "BBB"]})
        #
        # # Or modify the List of existing labels. The new label is unicode with no
        # # spaces
        # issue.fields.labels.append(u"new_text")
        # issue.update(fields={"labels": issue.fields.labels})
        #
        # # Linking a remote jira issue (needs applinks to be configured to work)
        # issue = jira.issue("JRA-1330")
        # issue2 = jira.issue("XX-23")  # could also be another instance
        # jira.add_remote_link(issue, issue2)
        return {"jira_issues": issues}
