import json


class RequestParser:
    def __init__(self, request_text=None):
        self._parser = ""
        if request_text and isinstance(request_text, dict):
            self._parser = json.dumps(request_text, indent=2)

    def _add_space(self):
        if self._parser:
            self._parser += "\n"

    def __add__(self, other):
        self._add_space()
        if not other:
            pass
        elif isinstance(other, dict):
            self._parser += json.dumps(other, indent=2)
        return self

    def __iadd__(self, other):
        self._add_space()
        if not other:
            pass
        elif isinstance(other, dict):
            self._parser += json.dumps(other, indent=2)
        return self

    def __str__(self):
        return self._parser
