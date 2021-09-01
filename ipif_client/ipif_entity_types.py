from functools import wraps


from dateutil.parser import *

from ipif_client.exceptions import IPIFClientConfigurationError, IPIFClientDataError
from ipif_client.ipif_queryset import IPIFQuerySet
from ipif_client.utils.bunch import Bunch
from ipif_client.utils.statements_container import Statements


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
        if getattr(self, "label", None):
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

        #### HERE... move all the requesting logic here... oh no... the
        ## request_id_from_endpoints needs to do all the grabbing of shit

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
            # print(f"about to get {name} from server")
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
        # print(r)
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
        o.statements = Statements(
            (
                cls._ipif_instance.Statements._init_from_ref_json(st_json)
                for st_json in r.get("statement-refs", [])
            )
        )
        return o

    @classmethod
    def _init_from_ref_json(cls, r):
        o = cls()
        o.id = r["@id"]
        o.source = cls._ipif_instance.Sources._init_from_ref_json(r.get("source-ref"))
        o.person = cls._ipif_instance.Persons._init_from_ref_json(r.get("person-ref"))
        o.statements = Statements(
            (
                cls._ipif_instance.Statements._init_from_ref_json(st_json)
                for st_json in r.get("statement-refs", [])
            )
        )
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
