import time
from functools import wraps

from munch import Munch as Bunch
from dateutil.parser import *
import math
import requests
from typing import Callable, Dict

from yaspin import yaspin
from yaspin.spinners import Spinners


class Bunch(Bunch):
    def __init__(self, varname, *args, **kwargs):
        self.__var_name = varname
        super().__init__(*args, **kwargs)

    def __repr__(self):
        keys = self.keys()

        # keys.sort()
        args = ", ".join(
            [
                "%s=%r" % (key, self[key])
                for key in keys
                if not key.startswith("_Bunch__")
            ]
        )
        return "%s: %s" % (self.__var_name, args)


class IPIFClientException(Exception):
    pass


class IPIFClientConfigurationError(IPIFClientException):
    pass


class IPIFClientQueryError(IPIFClientException):
    pass


class IPIFClientDataError(IPIFClientException):
    pass


class Statements(list):
    pass


class IPIFQuerySet:
    def __init__(self, search_params=None, *args, **kwargs):
        self._search_params = search_params or {}

    def _spawn_new_with_search_param(param: str):
        def inner_func(self, value):
            class_name = self.__class__.__name__.replace("sQuerySet", "")
            if param == class_name.lower() + "Id":
                raise IPIFClientQueryError(f"")

            return self.__class__(
                search_params={
                    **self._search_params,
                    param: value,
                }
            )

        return inner_func

    factoidId = _spawn_new_with_search_param("factoidId")
    f = _spawn_new_with_search_param("f")
    sourceId = _spawn_new_with_search_param("sourceId")
    s = _spawn_new_with_search_param("s")
    statementId = _spawn_new_with_search_param("statementId")
    st = _spawn_new_with_search_param("st")
    personId = _spawn_new_with_search_param("personId")
    p = _spawn_new_with_search_param("p")


class IPIFType:
    _ref_only = False

    def _proxy_to_new_queryset(method_name):
        """Define a method on IPIFType that creates a new QuerySet
        and calls the named method on that QuerySet (returning a new
        queryset)"""

        @classmethod
        @wraps(getattr(IPIFQuerySet, method_name))
        def inner(cls, *args, **kwargs):
            query_set = cls._queryset()
            query_set_method = getattr(query_set, method_name, None)
            return query_set_method(*args, **kwargs)

        return inner

    factoidId = _proxy_to_new_queryset("factoidId")
    f = _proxy_to_new_queryset("f")
    sourceId = _proxy_to_new_queryset("sourceId")
    s = _proxy_to_new_queryset("s")
    statementId = _proxy_to_new_queryset("statementId")
    st = _proxy_to_new_queryset("st")
    personId = _proxy_to_new_queryset("personId")
    p = _proxy_to_new_queryset("p")

    def __str__(self):
        if hasattr(self, "label"):
            return f"{self.__class__.__name__}: {self.label}"
        else:
            return f"{self.__class__.__name__}: {self.id}"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, name):
        return self._data_dict.get(name)

    @classmethod
    def _select_start_endpoint_and_dict(cls, resp_dict):
        """Determine which endpoint and associated data dict to choose
        from a result dict"""

        # If we have a preferred endpoint and that one has data,
        # use that
        if (
            cls._ipif_instance._preferred_endpoint
            and resp_dict.get(cls._ipif_instance._preferred_endpoint)
            and resp_dict.get(cls._ipif_instance._preferred_endpoint)
            != {"IPIF_STATUS": "Request failed"}
        ):
            start_dict = resp_dict.get(cls._ipif_instance._preferred_endpoint)
            start_endpoint_name = cls._ipif_instance._preferred_endpoint
        # Otherwise, just go through in order and pick the first endpoint dict
        # that has any data
        else:
            possible_dicts = [
                (e, resp_dict[e])
                for e in resp_dict
                if resp_dict[e] and resp_dict[e] != {"IPIF_STATUS": "Request failed"}
            ]
            if possible_dicts:
                start_endpoint_name, start_dict = possible_dicts[0]
            else:
                return None, None

        return start_endpoint_name, start_dict

    @classmethod
    def _reconcile_persons_from_id(cls, resp_dict):
        start_endpoint_name, start_dict = cls._select_start_endpoint_and_dict(resp_dict)
        if start_dict is None:
            return None, None

        if cls._ipif_instance._hound_mode:

            # Here, we get a list of all the other URIs available for this entity
            # and try endpoints that have returned None (or failed... again; why not?)
            # to see if we have any luck with this alternative URI
            alternative_uris_to_try = []
            for data in resp_dict.values():
                if data and data != {"IPIF_STATUS": "Request failed"}:
                    alternative_uris_to_try += data.get("uris", [])

            for endpoint_name, data in resp_dict.items():
                if not data or data == {"IPIF_STATUS": "Request failed"}:
                    # endpoint_name, ipif_type, id_string
                    for uri in alternative_uris_to_try:
                        resp = cls._ipif_instance._request_single_object_by_id(
                            endpoint_name, cls.__name__.lower() + "s", uri
                        )
                        if resp and resp != {"IPIF_STATUS": "Request failed"}:
                            resp_dict[endpoint_name] = resp

        # print(start_dict)
        for factoid in start_dict["factoid-refs"]:
            factoid["ipif-endpoint"] = start_endpoint_name

        for endpoint_name, data in resp_dict.items():
            if data.get("factoid-refs", None) and endpoint_name != start_endpoint_name:
                for factoid in data["factoid-refs"]:
                    factoid["ipif-endpoint"] = endpoint_name
                    start_dict["factoid-refs"].append(factoid)
                start_dict["uris"] = list(set([*start_dict["uris"], *data["uris"]]))

        return start_endpoint_name, start_dict

    @classmethod
    def id(cls, id_string):
        """Gets IPIF entity by @id from all endpoints. Combines Persons and Sources to
        a single entity."""

        resp = cls._ipif_instance._request_id_from_endpoints(
            cls.__name__.lower() + "s", id_string
        )

        # Don't just return the first one here... RECONCILE!
        if cls.__name__ in ("Statement", "Factoid"):
            items = [
                (endpoint_name, data)
                for endpoint_name, data in resp.items()
                if data and data != {"IPIF_STATUS": "Request failed"}
            ]
            if not items:
                return None
            if len(items) == 1:
                endpoint_name, data = items[0]
                return cls._init_from_id_json(data, endpoint_name=endpoint_name)
            if len(items) > 1:
                raise IPIFClientDataError(
                    f"More than one {cls.__name__} with id '{id_string}' was found."
                    "Try selecting from a specific endpoint with [MECHANISM NOT YET INVENTED]"
                )
        else:
            endpoint_name, data = cls._reconcile_persons_from_id(resp)
            if not data:
                return None
            return cls._init_from_id_json(
                data,
                endpoint_name=endpoint_name,
            )

    def __getattr__(self, name):
        """If an IPIFType is a -ref, i.e. not full data,
        and user attempts to get an attribute.


        REMEMBER: anything that even hits this function does
        so because it *does not exist*"""

        if name == "label":
            return self.id
        if name.startswith("_"):
            return

        if self._ref_only:
            print(f"about to get {name} from server")
            # Get from server
            new = self.get_by_id(self.id)

            if new:
                return_value = getattr(new, name)
                self.__dict__.update(new.__dict__)

                if return_value:
                    return return_value

                else:
                    raise AttributeError
            else:
                raise AttributeError
        raise AttributeError

    @classmethod
    def _init_from_id_json(cls, r, endpoint_name):
        print(r)
        o = cls()
        o._ref_only = False  # if full object, not just ref_only

        o.get_by_id = cls.id
        o.id = f"{endpoint_name}::{r['@id']}"

        o.local_id = r["@id"]
        o.label = r.get("label", None)
        o.uris = r.get("uris", [])
        o.createdBy = r.get("createdBy", "")
        o.createdWhen = (
            parse(r["createdWhen"].replace("Z", "")) if "createdWhen" in r else None
        )

        o.modifiedBy = r.get("modifiedBy", "")
        o.modifiedWhen = (
            parse(r["modifiedWhen"].replace("Z", "")) if "modifiedWhen" in r else None
        )

        if cls.__name__ != "Factoid":
            o.factoids = [
                cls._ipif_instance.Factoids._init_from_ref_json(f_json)
                for f_json in r.get("factoid-refs", [])
            ]

        o._data_dict = r

        return o

    @classmethod
    def _init_from_ref_json(cls, r):
        o = cls()
        o._ref_only = True  # Initted as X-ref only

        o.get_by_id = cls.id
        o.id = r["@id"]

        return o


class IPIFFactoids(IPIFType):
    @classmethod
    def _init_from_id_json(cls, r, endpoint_name):
        o = super()._init_from_id_json(r, endpoint_name=endpoint_name)
        o.source = cls._ipif_instance.Sources._init_from_ref_json(r.get("source-ref"))
        o.person = cls._ipif_instance.Persons._init_from_ref_json(r.get("person-ref"))
        o.statements = [
            cls._ipif_instance.Statements._init_from_ref_json(st_json)
            for st_json in r.get("statement-refs", [])
        ]
        return o

    @classmethod
    def _init_from_ref_json(cls, r):
        o = cls()
        o.id = r["@id"]
        o.source = cls._ipif_instance.Sources._init_from_ref_json(r.get("source-ref"))
        o.person = cls._ipif_instance.Persons._init_from_ref_json(r.get("person-ref"))
        o.statements = [
            cls._ipif_instance.Statements._init_from_ref_json(st_json)
            for st_json in r.get("statement-refs", [])
        ]
        return o


class IPIFPersons(IPIFType):
    pass


class IPIFSources(IPIFType):
    pass


class IPIFStatements(IPIFType):
    @classmethod
    def _init_from_id_json(cls, r, endpoint_name):
        # print(r)
        o = super()._init_from_id_json(r, endpoint_name=endpoint_name)
        o.statementType = Bunch("StatementType", r.get("statementType", {})) or None
        o.name = r.get("name", None)
        o.memberOf = Bunch("MemberOf", r.get("memberOf", {})) or None
        o.role = Bunch("Role", r.get("role", {})) or None

        date = r.get("date", {})
        sortdate = date.get("sortdate", None)
        parsed_sortdate = parse(sortdate).replace(tzinfo=None) if sortdate else None
        date_label = date.get("label")

        o.date = Bunch("Date", {"sortdate": parsed_sortdate, "label": date_label})

        o.statementText = r.get("statementText", None)

        o.places = [Bunch("Place", p) for p in r.get("places", [])]
        o.relatesToPersons = [Bunch("Person", p) for p in r.get("relatesToPersons", [])]
        return o


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
    def _request_id_from_endpoints(self, ipif_type, id_string):
        results = {}
        with yaspin(Spinners.arc, color="magenta", timer=True, text="Loading...") as sp:
            for endpoint_name in self._endpoints:
                sp.text = f"Getting {ipif_type} @id='{id_string}' from {endpoint_name}"

                result = self._request_single_object_by_id(
                    endpoint_name, ipif_type, id_string
                )
                if result:
                    results[endpoint_name] = result

                if result and result != {"IPIF_STATUS": "Request failed"}:
                    sp.ok("✅ ")
                else:
                    sp.fail("💥 ")

        return results

    @_error_if_no_endpoints
    def _base_query_request(
        self, endpoint_name, ipif_type, search_params, statement_params={}
    ):
        URL = f"{self._endpoints[endpoint_name]}{ipif_type.lower()}"

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
        pass


def timeout_wrapper(t):
    time.sleep(t)
