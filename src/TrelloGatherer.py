import json
from GithubGatherer import open_url_element


class TrelloGatherer:
    def __init__(self, url, credentials):
        self.url_request = url

    def request(self):
        dumped = open_url_element(self.url_request, None)
        dumped = json.loads(dumped)
        # for dump in dumped:
        #     if "card" in dump["data"]:
        #         print(dump["data"]["board"], dump["data"]["card"])
        #     else:
        #         print(dump["data"]["board"])
        return {"trello_events": dumped}
