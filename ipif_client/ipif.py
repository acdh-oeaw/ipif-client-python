import math
import time
from typing import Dict

import requests
from yaspin import yaspin
from yaspin.spinners import Spinners


from ipif_client.exceptions import IPIFClientConfigurationError
from ipif_client.ipif_entity_types import (
    IPIFFactoids,
    IPIFPersons,
    IPIFSources,
    IPIFStatements,
)
from ipif_client.ipif_queryset import IPIFQuerySet


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
    def _build_queryset_class(self, qs_class_name):
        """Creates an IPIFQuerySet subclass type to be bound to
        an IPIF instance, giving access via _ipif_instance variable
        back to the instance of this class"""
        return type(
            qs_class_name,
            (IPIFQuerySet,),
            {"_ipif_instance": self},
        )

    def __init__(self, config={}):
        """Create a new IPIF client.

        Pass config dict with options:
        "endpoints": {"name": "SHORT_NAME", "uri": "URI OF ENDPOINT"}
        """
        self._DEFAULT_PAGE_REQUEST_SIZE = 30

        self._endpoints = {}
        self._preferred_endpoint = None
        self._hound_mode = True

        # Dict for caching responses. Maybe make this a class so we're not
        # having to do loads of dict methods on it, and can change the
        # implememntation
        self._data_cache: Dict = {}

        # Unpack endpoints from config into instance's endpoint dict
        if "endpoints" in config:
            for label, endpoint in config["endpoints"].items():
                self.add_endpoint(name=label, uri=endpoint)

        # Create IPIF-type classes on the instance
        # each instance has its own classes, so class itself holds reference back
        # to this class. (This so so we can do ipif.Person.id() etc. in Django fashion;
        # but also keep each of these classes bound to their IPIF instance)
        self.Persons = type("Person", (IPIFPersons,), {"_ipif_instance": self})
        self.Statements = type("Statement", (IPIFStatements,), {"_ipif_instance": self})
        self.Factoids = type("Factoid", (IPIFFactoids,), {"_ipif_instance": self})
        self.Sources = type("Source", (IPIFSources,), {"_ipif_instance": self})

        # Also set up a QuerySet and add it to the class for reference
        self._PersonsQuerySet = self._build_queryset_class("PersonsQuerySet")
        self.Persons._queryset = self._PersonsQuerySet

        self._StatementsQuerySet = self._build_queryset_class("StatementsQuerySet")
        self.Statements._queryset = self._StatementsQuerySet

        self._FactoidsQuerySet = self._build_queryset_class("FactoidsQuerySet")
        self.Factoids._queryset = self._FactoidsQuerySet

        self._SourcesQuerySet = self._build_queryset_class("SourcesQuerySet")
        self.Sources._queryset = self._SourcesQuerySet

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
        if (
            endpoint_name,
            ipif_type,
            id_string,
        ) in self._data_cache and self._data_cache[
            (endpoint_name, ipif_type, id_string)
        ] != {
            "IPIF_STATUS": "Request failed"
        }:
            return self._data_cache[(endpoint_name, ipif_type, id_string)]

        URL = f"{self._endpoints[endpoint_name]}{ipif_type.lower()}/{id_string}"
        # print(f"Getting {URL}...")
        try:
            resp = requests.get(URL)

        except requests.exceptions.ConnectionError:
            self._data_cache[(endpoint_name, ipif_type, id_string)] = {
                "IPIF_STATUS": "Request failed"
            }
            return {"IPIF_STATUS": "Request failed"}

        if resp.status_code == 200:
            data = resp.json()
            self._data_cache[(endpoint_name, ipif_type, id_string)] = data
            return data
        elif resp.status_code == 404:
            self._data_cache[(endpoint_name, ipif_type, id_string)] = None
            return None
        else:
            self._data_cache[(endpoint_name, ipif_type, id_string)] = {
                "IPIF_STATUS": "Request failed"
            }
            return {"IPIF_STATUS": "Request failed"}

    @_error_if_no_endpoints
    def _request_id_from_endpoints(self, ipif_type, id_string, specify_endpoints=set()):
        results = {}

        endpoints_to_get = specify_endpoints or self._endpoints

        with yaspin(Spinners.earth, color="magenta", timer=True) as sp:
            for endpoint_name in endpoints_to_get:
                sp.text = f"Getting {ipif_type} @id='{id_string}' from {endpoint_name}"

                result = self._request_single_object_by_id(
                    endpoint_name, ipif_type, id_string
                )
                if result:
                    results[endpoint_name] = result

                if result and result != {"IPIF_STATUS": "Request failed"}:
                    sp.ok("✅ ")
                    pass
                else:
                    sp.fail("💥 ")
                    pass

        return results

    @_error_if_no_endpoints
    def _base_query_request(
        self, endpoint_name, ipif_type, search_params, statement_params={}
    ):
        URL = f"{self._endpoints[endpoint_name]}{ipif_type.lower()}"

        # CACHE IT HERE SO WE DON'T NEED TO WORRY ELSEWHERE.

        try:

            resp = requests.get(URL, params=search_params)
            # print(resp.url)
            # print(resp.status_code)
        except requests.exceptions.ConnectionError:
            return None

        if resp.status_code == 200:
            # Unlike getting the ID, we actually want to return the
            # results set, even if empty
            return resp.json()
        else:
            return None

    @_error_if_no_endpoints
    def _iterate_results_from_single_endpoint(
        self, endpoint_name, ipif_type, search_params, statement_params={}
    ):
        page = 1
        size = self._DEFAULT_PAGE_REQUEST_SIZE

        sps = {**search_params, "page": page, "size": size}

        for _ in range(5):
            first_response = self._base_query_request(endpoint_name, ipif_type, sps)
            if first_response:
                yield from first_response[ipif_type.lower()]
                break
            timeout_wrapper(1)
        else:
            yield {"IPIF_STATUS": "Request failed"}
            return

        totalHits = first_response["protocol"]["totalHits"]
        numberPages = math.ceil(totalHits / size)

        for page_num in range(2, numberPages + 1):
            sps = {**search_params, "page": page_num, "size": size}
            for _ in range(5):
                response = self._base_query_request(endpoint_name, ipif_type, sps)
                if response:
                    yield from response[ipif_type.lower()]
                    break
                timeout_wrapper(1)
            else:
                yield {"IPIF_STATUS": f"Request failed for page {page_num}"}
                return

    @_error_if_no_endpoints
    def _query_request_from_endpoints(
        self, ipif_type, search_params, statement_params={}
    ):
        results = {}

        with yaspin(Spinners.earth, color="magenta", timer=True) as sp:

            for endpoint_name in self._endpoints:
                sp.text = f"Searching for {ipif_type} with {str(search_params)}, {str(statement_params)} from {endpoint_name}"
                result = list(
                    self._iterate_results_from_single_endpoint(
                        endpoint_name, ipif_type, search_params, statement_params
                    )
                )
                if result:
                    results[endpoint_name] = result

        return results


def timeout_wrapper(t):
    time.sleep(t)
