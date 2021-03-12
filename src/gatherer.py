from abc import ABC, abstractmethod
from constants import TOKEN_AUTH, USER_AUTH, JSON_AUTH


class Gatherer(ABC):
    def __init__(self, url, credentials):
        self.url_request = url
        self.authorization_header = credentials.get(USER_AUTH, {})
        if USER_AUTH in credentials:
            # Curl -i user credentials
            self.authorization_header = credentials[USER_AUTH][2]
        elif TOKEN_AUTH in credentials:
            # Curl change header -H authorization
            self.authorization_header = {'Authorization':
                                          credentials[TOKEN_AUTH]}

    @abstractmethod
    def parse_response(self, request_type, response):
        pass

    @abstractmethod
    def request(self):
        pass
