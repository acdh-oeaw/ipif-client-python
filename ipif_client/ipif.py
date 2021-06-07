import requests
from typing import Callable


class IPIFClientConfigurationError(Exception):
    pass


class IPIFType:
    pass


class IPIFPerson(IPIFType):
    pass


class IPIFStatement(IPIFType):
    pass


class IPIFFactoid(IPIFType):
    pass


class IPIFSource(IPIFType):
    pass


def _error_if_no_endpoints(func):
    """Decorator for IPIF request methods to raise error
    if no endpoints are set."""

    def inner(self, *args, **kwargs):
        if self._endpoints:
            return func(self, *args, **kwargs)

        else:
            raise IPIFClientConfigurationError("No endpoints added to the IPIF client")

    return inner


class IPIF:
    def __init__(self, config={}):
        self._endpoints = {}

        # Unpack endpoints from config into instance's endpoint dict
        if "endpoints" in config:
            for label, endpoint in config["endpoints"].items():
                self.add_endpoint(name=label, uri=endpoint)

        # Create IPIF-type classes on the instance
        # each instance has its own classes, so class itself holds reference back
        # to this class. (This so so we can do ipif.Person.id() etc. in Django fashion;
        # but also keep each of these classes bound to their IPIF instance)
        self.Person = type("Person", (IPIFPerson,), {"_ipif_instance": self})
        self.Statement = type("Statement", (IPIFStatement,), {"_ipif_instance": self})
        self.Factoid = type("Factoid", (IPIFFactoid,), {"_ipif_instance": self})
        self.Source = type("Source", (IPIFSource,), {"_ipif_instance": self})

    def add_endpoint(self, name=None, uri=None):
        if not name or not uri:
            raise IPIFClientConfigurationError(
                "An IPIF endpoint requires a label and endpoint uri"
            )

        if name in self._endpoints:
            raise IPIFClientConfigurationError(
                f"An endpoint with label '{name}' has already been added. "
                "If this is a different endpoint, assign a unique label."
            )

        if uri in self._endpoints.values():
            raise IPIFClientConfigurationError(
                f"Endpoint '{uri}' has already been added."
            )

        self._endpoints[name] = uri

    @_error_if_no_endpoints
    def _request_single_object_by_id(self, endpoint_name, ipif_type, id_string):

        URL = f"{self._endpoints[endpoint_name]}{ipif_type.lower()}/{id_string}"
        print(URL)
        try:
            resp = requests.get(URL)
        except requests.exceptions.ConnectionError:
            return {"IPIF_STATUS": "Request failed"}

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            return {"IPIF_STATUS": "Request failed"}

    @_error_if_no_endpoints
    def _request_id_from_endpoints(self, ipif_type, id_string):
        results = {}
        for endpoint_name, endpoint_uri in self._endpoints.items():
            result = self._request_single_object_by_id(
                endpoint_name, ipif_type, id_string
            )
            if result:
                results[endpoint_name] = result

        return results
