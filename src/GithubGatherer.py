import itertools
import json
import re
import urllib3
from urllib3.exceptions import HTTPError
from gatherer import Gatherer
from constants import API_LIMIT_EXCEEDED


class GithubGatherer(Gatherer):
    URL = "url"
    TAGS_URL = "tags_url"
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

    def gather(self, request, resource, strip=False):
        dumped_data = open_url_element(request, resource, strip,
                                       self.authorization_header)
        array_dict = json.loads(dumped_data)
        return array_dict

    def parse_request(self, request_type, request):
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
            parser['tags'] = {'name': request['name'],
                              'url': request["commit"]["url"]}
        elif request_type is self.CONTRIBUTORS_URL:
            contributors = itertools.chain.from_iterable(request.values())
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
            pass
        return parser

    def get_contributors_info(self, contributors):
        output = []
        for contributor in contributors:
            contributors_request = contributor[self.URL]
            contributors_info = self.gather(contributors_request,
                                            None)
            contributors_repos = self.gather(contributors_request,
                                             self.REPOS_URL)
            # Add contributors info to repositories
            contributors_repos.insert(0, contributors_info)
            output.append({contributors_info["login"]: contributors_repos})
            break
        return output

    def request(self):
        # Setup concrete url or opener based on the authentication process
        tags = self.gather(self.url_request, self.TAGS_URL)
        contributors = self.gather(self.url_request, self.CONTRIBUTORS_URL)
        contributors = self.get_contributors_info(contributors)
        commits = self.gather(self.url_request, self.COMMITS_URL, True)
        return {self.TAGS_URL: tags,
                self.CONTRIBUTORS_URL: contributors,
                self.COMMITS_URL: commits}


def open_url_element(url, element, strip=False, header={}):
    https = urllib3.PoolManager()
    try:
        response = https.request('GET', url, headers=header)
    except HTTPError as error:
        error_type = error.read().decode('utf-8')
        if API_LIMIT_EXCEEDED in error_type:
            pass
        raise
    dict_output = json.loads(response.data.decode('utf-8'))
    if element in dict_output:
        new_url = dict_output[element]
        if strip:
            new_url = re.search('.*(?<=\{)', new_url).group(0)[:-1]
        # Create request from new url containing authorization header
        response_element = https.request('GET', new_url, headers=header)
        element_output = json.loads(response_element.data.decode('utf-8'))
        return json.dumps(element_output, indent=2)
    return json.dumps(dict_output, indent=2)

