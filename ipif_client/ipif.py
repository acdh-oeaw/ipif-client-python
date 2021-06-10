from functools import wraps
from bunch import Bunch
from dateutil.parser import *
import requests
from typing import Callable, Dict


class IPIFClientException(Exception):
    pass


class IPIFClientConfigurationError(IPIFClientException):
    pass


class IPIFClientQueryError(IPIFClientException):
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
    _data_cache: Dict = {}

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

    def __getattribute__(self, name):
        # Don't do it like this!!!
        # Use a 'is_only_ref' flag... then grab the real object
        # and swap them out!!
        if object.__getattribute__(self, name):
            return object.__getattribute__(self, name)
        else:
            return "GO GET FROM SERVER"

    @classmethod
    def id(cls, id_string):
        resp = cls._ipif_instance._request_id_from_endpoints(
            cls.__name__.lower() + "s", id_string
        )
        cls._data_cache[id_string] = resp

        for endpoint_name, data in resp.items():
            return cls._init_from_id_json(data, endpoint_name=endpoint_name)

    @classmethod
    def _init_from_id_json(cls, r, endpoint_name):
        # print(r)
        o = cls()
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
        o = super()._init_from_id_json(r, endpoint_name=endpoint_name)
        o.statementType = Bunch(r.get("statementType", {})) or None
        o.name = r.get("name", None)
        o.memberOf = Bunch(r.get("memberOf", {})) or None
        o.role = Bunch(r.get("role", {})) or None
        o.date = Bunch(r.get("date", {})) or None
        o.date.sortdate = parse(o.date.sortdate).replace(tzinfo=None)
        o.statementText = r.get("statementText", None)

        o.places = [Bunch(p) for p in r.get("places", [])]
        o.relatesToPersons = [Bunch(p) for p in r.get("relatesToPersons", [])]

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
        self._endpoints = {}

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

        URL = f"{self._endpoints[endpoint_name]}{ipif_type.lower()}/{id_string}"
        print(f"Getting {URL}...")
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
        for endpoint_name in self._endpoints:
            result = self._request_single_object_by_id(
                endpoint_name, ipif_type, id_string
            )
            if result:
                results[endpoint_name] = result

        return results
