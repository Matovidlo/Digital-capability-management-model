from abc import ABC
from request_parser import RequestParser


class Request(ABC):
    """
    The Target defines the domain-specific interface used by the client code.
    """

    def send_requests(self) -> tuple:
        return ("Target: The default target's behavior.")


class APIAdapter(Request):
    """
    The Adapter makes the Adaptee's interface compatible with the Target's
    interface via multiple inheritance.
    """
    GATHERER = ".*(?=Gatherer)"
    def __init__(self, gatherer):
        self._gatherer = gatherer

    @property
    def gatherer(self):
        return self._gatherer

    @gatherer.setter
    def gatherer(self, gatherer):
        self._gatherer = gatherer

    def get_requests_important_items(self, requests):
        parsed = RequestParser()
        output = []
        for request_type, request in requests.items():
            for entry in request:
                # Parse request is implemented
                if "parse_response" in dir(self._gatherer):
                    result = self._gatherer.parse_response(request_type, entry)
                    if result:
                        output.append(result)
                        parsed += result
                # Otherwise append whole entry
                else:
                    if entry:
                        output.append(entry)
                        parsed += str(entry)
        # fixme: remove printing parsed data when parsing is correct
        return output

    def send_requests(self) -> list:
        requests = self.gatherer.send_request()
        output = self.get_requests_important_items(requests)
        return output
