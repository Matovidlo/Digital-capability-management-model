import copy
import itertools
import logging
import json
import re
import urllib3
from urllib3.exceptions import HTTPError
from gatherer import Gatherer
from constants import API_LIMIT_EXCEEDED


class GithubGatherer(Gatherer):
    URL = "url"
    TAGS_URL = "tags_url"
    MILESTONES_URL = "milestones_url"
    ISSUES_URL = "issues_url"
    CONTRIBUTORS_URL = "contributors_url"
    REPOS_URL = "repos_url"
    COMMITS_URL = "commits_url"
    HAS_ISSUES = "has_issues"
    HAS_WIKI = "has_wiki"

    def __init__(self, repository, credentials):
        super(GithubGatherer, self).__init__(repository, credentials)

    def gather_for_dump(self, request, resource, strip):
        return open_url_element(request, resource, strip,
                                self.authorization_header)

    def gather(self, request, resource, strip=False, options={},
               multipage=False):
        array_dict = None
        if multipage:
            old_data = None
            dumped_data = []
            options['page'] = 1
            while True:
                if old_data is dumped_data:
                    break
                for repository in request:
                    dumped_data = open_url_element(repository, resource, strip,
                                                   self.authorization_header,
                                                   options)
                    old_data = copy.deepcopy(dumped_data)
                    options['page'] += 1
                    if isinstance(array_dict, list):
                        array_dict += json.loads(dumped_data)
                    else:
                        array_dict = json.loads(dumped_data)
        else:
            for repository in request:
                dumped_data = open_url_element(repository, resource, strip,
                                               self.authorization_header,
                                               options)
                if isinstance(array_dict, list):
                    array_dict += json.load(dumped_data)
                else:
                    array_dict = json.loads(dumped_data)
        return array_dict

    def filter_issue_description(self, value):
        # Remove https links
        value = re.sub(r'https?:\/\/.*\]', '', value)
        # Remove https links
        value = re.sub(r'https?:\/\/.*\n', '', value)
        # Remove https links
        value = re.sub(r'https?:\/\/.*', '', value)
        # Filter debug output of the execution
        value = re.sub(r'\[?[A-Z]+[- ]\d+\]?', '', value, flags=re.MULTILINE)
        # Remove html tags
        # value = re.sub(r'<.*\/>\n', '', value, flags=re.S)
        # Remove code segments
        value = re.sub(
            r'^\{code((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{code\}',
            '', value, flags=re.MULTILINE)
        # todo: is it necessary to remove quote segment? They just highlight
        # Remove quote segments
        # value = re.sub(r'^\{quote((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{quote\}',
        #                '', value, flags=re.MULTILINE)
        # Remove noformat segments
        value = re.sub(
                r'^\{noformat((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{noformat\}',
                '', value, flags=re.MULTILINE)
        # Remove xml tags
        # value = re.sub(r'<\w+>.*<\/\w+>\n', '', value, flags=re.S)
        # At reports from scala removed
        value = re.sub(r'(\s)?at (\w+\S+)\(.*\.\w+:\d+\)\n', '', value,
                       flags=re.MULTILINE)
        # Filter datetimes from output. It is necessary since date does not influence
        # training in positive but rather negative way.
        value = re.sub(r'((\d{4})-(\d{2})-(\d{2})|'
                       r'(\d{4})\/(\d{2})\/(\d{2}))'
                       r' (\d{2}):(\d{2}):(\d{2})(\.\d+)?', '', value)
        # Remove HTML comments and github code samples
        value = re.sub(r'\{[\s\S]*?\}', '', value)
        value = re.sub(r'<!--[\s\S]*?-->', '', value)
        value = re.sub(r'```[\s\S]*?```', '', value)
        # value = re.sub(r'(?<=(info|error|Exception))(\s+(\(|\[)((\w+|\d+)(-|\.|_|=|\]|\)|,\s|\s))*)*',
        #                '', value)
        value = re.sub(r'\((\d+(,)?(\s)?(\)\.\.\.)?)+', '', value)
        # Remove github markdown issuing steps
        value = re.sub(r'\*\*(\w+(\s|:|\/|\'|\!))*(\w+)?', '', value)
        if not value or len(value.split()) < 20:
            return ''
        return value

    def parse_response(self, request_type, response):
        # Github repository tags URL: ["name"], ["commit"]["url"]
        # Github repository contributors URL: ["name"], ["login"],
        #                                     ["avatar_url"], ["company"], ["email"]
        # Github repository contributors repositories: ["name"],
        #                                              ["owner"]["login"]
        #                                              ["description"], ["created_at"],
        #                                              ["updated_at"], ["language"],
        #                                              ["has_issues"], ["has_wiki"],
        #                                              ["open_issues"]
        # Github repository commits: ["commit"]["author"]["name"],
        #                            ["commit"]["author"]["email"],
        #                            ["commit"]["author"]["date"], ["commit"]["message"],
        #                            ["author"]["login"], ["author"]["avatar_url"]
        #                            list(["parents"])
        # todo:
        #  avatars could be merged for the same author name or author login.
        parser = {}
        if request_type is self.TAGS_URL:
            parser['tags'] = {'name': response['name'],
                              'url': response["commit"]["url"]}
        elif request_type is self.CONTRIBUTORS_URL:
            contributors = itertools.chain.from_iterable(response.values())
            contributor_name = None
            for contributor in contributors:
                # Parse single contributor repositories
                if "owner" in contributor:
                    repository = contributor["name"].replace('.', '#')
                    parser[contributor_name][repository] =\
                        {'owner': True,
                         'login': contributor["owner"]["login"],
                         'avatar_url': contributor["owner"]["avatar_url"],
                         'description': contributor["description"],
                         'created': contributor["created_at"],
                         'updated': contributor["updated_at"],
                         'language': contributor["language"],
                         'has_wiki': contributor[self.HAS_WIKI],
                         'open_issues': contributor["open_issues"]}
                # Parse contributor information
                else:
                    contributor_name = contributor['name']
                    parser[contributor["name"]] =\
                        {'login': contributor["login"],
                         'avatar_url': contributor["avatar_url"],
                         'company': contributor["company"],
                         'email': contributor['email']}
        elif request_type is self.COMMITS_URL:
            parser = {'commits': ''}
        elif request_type is self.ISSUES_URL:
            # description = self.filter_issue_description(response['body'])
            # fixme: choose one
            description = response['body']
            parser = \
                {'comments_url': response['comments_url'],
                 'labels': response['labels'],
                 'number': response['number'],
                 'title': response['title'],
                 'id': response['id'],
                 'user': response['user'],
                 'state': response['state'],
                 'assignee': response['assignee'],
                 'assignees': response['assignees'],
                 'milestone': response['milestone'],
                 'comments': response['comments'],
                 'created_at': response['created_at'],
                 'updated_at': response['updated_at'],
                 'closed_at': response['closed_at'],
                 'description': description
                 }
        return parser

    def get_contributors_info(self, contributors):
        output = []
        for contributor in contributors:
            try:
                contributors_request = contributor[self.URL]
            except TypeError:
                print("Received message from repository: {}".format(contributors))
                print("The problem lays probably in incorrect url of repository")
                raise
            contributors_info = self.gather([contributors_request],
                                            None)
            contributors_repos = self.gather([contributors_request],
                                             self.REPOS_URL)
            # Add contributors info to repositories
            contributors_repos.insert(0, contributors_info)
            output.append({contributors_info["login"]: contributors_repos})
            break
        return output

    def send_request(self):
        # Setup concrete url or opener based on the authentication process
        options = {"per_page": 100}
        issues = self.gather(self.url_request, self.ISSUES_URL,
                             True, options=options, multipage=True)
        contributors = self.gather(self.url_request, self.CONTRIBUTORS_URL)
        contributors = self.get_contributors_info(contributors)
        commits = self.gather(self.url_request, self.COMMITS_URL, True)
        return {self.ISSUES_URL: issues,
                self.CONTRIBUTORS_URL: contributors,
                self.COMMITS_URL: commits}


def open_url_element(url, element, strip=False, header={}, options={}):
    https = urllib3.PoolManager()
    try:
        response = https.request('GET', url, headers=header)
    except HTTPError as error:
        error_type = error.args()[0]
        if API_LIMIT_EXCEEDED in error_type:
            pass
        raise
    dict_output = json.loads(response.data.decode('utf-8'))
    if element in dict_output:
        new_url = dict_output[element]
        if strip:
            new_url = re.search('.*(?<=\{)', new_url).group(0)[:-1]
        # Create request from new url containing authorization header
        response_element = https.request('GET', new_url, headers=header, fields=options)
        element_output = json.loads(response_element.data.decode('utf-8'))
        if not element_output:
            logging.warning('No ' + element[:-4] + ' were found inside repository ,,' + url + '\'\'')
        return json.dumps(element_output, indent=2)
    return json.dumps(dict_output, indent=2)

