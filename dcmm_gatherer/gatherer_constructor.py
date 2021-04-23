import importlib


class GathererConstructor:
    def __init__(self):
        pass

    def construct(self, gatherer_type, url, credentials):
        gatherer_type += "Gatherer"
        # Load specific module based on the gatherer type string
        gathererClass = getattr(importlib.import_module(gatherer_type),
                          gatherer_type)
        # Instantiate the class (pass arguments to the constructor, if needed)
        instance = gathererClass(url, credentials)
        return instance