# Existing tools that communicates trought API.
GITHUB = "Github"
GOOGLE_CALENDAR = "GoogleCalendar"
TRELLO = "Trello"
JIRA = "Jira"

TOKEN_AUTH = 'token'
USER_AUTH = 'user'
JSON_AUTH = 'JSON'
HTTP_AUTH = 'http'

# Authorization techniques
NO_CREDENTIALS = {}
REPOSITORIES = []
TOKEN_CREDENTIALS = {TOKEN_AUTH: ['{token}', '{header}']}
USER_CREDENTIALS = {USER_AUTH: ['{username}', '{password}', '{header}']}
JSON_CREDENTIALS = {JSON_AUTH: ['{file_path}', '{header}']}
HTTP_CREDENTIALS = {HTTP_AUTH: '{http_path}'}

GITHUB_API = 'https://api.github.com/repos/'
# Possible error messages received from APIs
API_LIMIT_EXCEEDED = "API rate limit exceeded"
gathering_urls = {GITHUB: (REPOSITORIES,
                           USER_CREDENTIALS),
                  GOOGLE_CALENDAR: ('', JSON_CREDENTIALS),
                  JIRA: ('http://localhost:8001',
                       USER_CREDENTIALS),
                  TRELLO: (HTTP_CREDENTIALS, NO_CREDENTIALS)
                 }
COMMON_ISSUE_TYPES = {
    'New Feature': ['FEATURE', 'NEW-FEATURE', 'NEW_FEATURE', 'NEW FEATURE'],
    'Improvement': ['ENHANCEMENT', 'IMPROVEMENT', 'DOC', 'DOCUMENTATION'],
    'Test': ['TEST'],
    'Bug': ['BUG'], }
