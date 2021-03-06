from constants import USER_AUTH
from gatherer_constructor import GathererConstructor
from API_adapter import APIAdapter


class APICommunicator:
    GATHERERES_TYPES = ["Github", "GoogleCalendar", "Trello", "Jira"]

    def __init__(self, urls_and_credentials):
        self._resources = []
        self._gatherer_constructor = GathererConstructor()
        self._adapters = []
        if isinstance(urls_and_credentials, dict):
            self.gathering_urls = urls_and_credentials

    @property
    def resources(self):
        return self._resources

    @resources.setter
    def resources(self, resources):
        self._resources.append(resources)

    def communicate(self, gatherer_type, url, credentials):
        for gatherer_constant in self.GATHERERES_TYPES:
            if gatherer_constant in gatherer_type:
                gatherer = self._gatherer_constructor.construct(gatherer_constant,
                                                                url,
                                                                credentials)
                adapter = APIAdapter(gatherer)
                self._adapters.append(gatherer_type)
                output = adapter.send_requests()
                return output
        return []

    def gather_resources(self):
        for gatherer_type, url_and_credentials in self.gathering_urls.items():
            url = url_and_credentials[0]
            credentials = None
            if len(url_and_credentials) > 1:
                credentials = url_and_credentials[1]
            self.resources = self.communicate(gatherer_type, url, credentials)

    def create_transactions(self, db):
        for collection, resource in zip(self._adapters, self._resources):
            db.write_data(resource, collection)

    def update_transactions(self, data, model_data, db, set_key=None):
        for collection in self._adapters:
            db.update_data(data, model_data, collection)

    def __str__(self):
        communications = ""
        for resource in self._resources:
            communications += str(resource) + "\n"
        return communications

