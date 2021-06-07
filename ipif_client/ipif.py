class IPIFClientConfigurationError(Exception):
    pass


class IPIF:
    def __init__(self, config={}):
        self._endpoints = {}

        if "endpoints" in config:
            for label, endpoint in config["endpoints"].items():
                self.add_endpoint(label=label, uri=endpoint)

    def add_endpoint(self, label=None, uri=None):
        if not label or not uri:
            raise IPIFClientConfigurationError(
                "An IPIF endpoint requires a label and endpoint uri"
            )

        if label in self._endpoints:
            raise IPIFClientConfigurationError(
                f"An endpoint with label '{label}' has already been added. "
                "If this is a different endpoint, assign a unique label."
            )

        if uri in self._endpoints.values():
            raise IPIFClientConfigurationError(
                f"Endpoint '{uri}' has already been added."
            )

        self._endpoints[label] = uri
