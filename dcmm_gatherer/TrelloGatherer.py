import json
from gatherer import Gatherer
from GithubGatherer import open_url_element


class TrelloGatherer(Gatherer):
    def __init__(self, url, credentials):
        self.url_request = url

    def send_request(self):
        # Trello: ["data"]["card"]["name"] ["data"]["list"]["name"] ["data"]["board"]["name"]
        #         type, date, memberCreator["username"]
        # No URL present
        if not self.url_request:
            print('No trello request was made')
            return {"trello_events": []}
        dumped = open_url_element(self.url_request, None)
        dumped = json.loads(dumped)
        # for dump in dumped:
        #     if "card" in dump["data"]:
        #         print(dump["data"]["board"], dump["data"]["card"])
        #     else:
        #         print(dump["data"]["board"])
        return {"trello_events": dumped}

    def parse_response(self, request_type, response):
        return response
