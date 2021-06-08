import requests
from typing import Callable, Dict


class IPIFClientConfigurationError(Exception):
    pass


class IPIFType:
    _data_cache: Dict = {}

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
        o.modifiedBy = r.get("modifiedBy", "")

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


class IPIFPersons(IPIFType):

    # Inherity _init_from_id_json

    pass


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
        o.statements = [
            cls._ipif_instance.Statements._init_from_ref_json(st_json)
            for st_json in r.get("statement-refs", [])
        ]
        o.source = cls._ipif_instance.Sources._init_from_ref_json(r.get("source-ref"))
        o.person = cls._ipif_instance.Persons._init_from_ref_json(r.get("person-ref"))

        return o


class IPIFStatements(IPIFType):
    pass


class IPIFSources(IPIFType):
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
        self.Persons = type("Person", (IPIFPersons,), {"_ipif_instance": self})
        self.Statements = type("Statement", (IPIFStatements,), {"_ipif_instance": self})
        self.Factoids = type("Factoid", (IPIFFactoids,), {"_ipif_instance": self})
        self.Sources = type("Source", (IPIFSources,), {"_ipif_instance": self})

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
