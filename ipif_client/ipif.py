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


class IPIF:
    def __init__(self, config={}):
        self._endpoints = {}

        # Unpack endpoints from config into instance's endpoint dict
        if "endpoints" in config:
            for label, endpoint in config["endpoints"].items():
                self.add_endpoint(label=label, uri=endpoint)

        # Create IPIF-type classes on the instance
        # each instance has its own classes, so class itself holds reference back
        # to this class. (This so so we can do ipif.Person.id() etc. in Django fashion;
        # but also keep each of these classes bound to their IPIF instance)
        self.Person = type("Person", (IPIFPerson,), {"_ipif_instance": self})
        self.Statement = type("Statement", (IPIFStatement,), {"_ipif_instance": self})
        self.Factoid = type("Factoid", (IPIFFactoid,), {"_ipif_instance": self})
        self.Source = type("Source", (IPIFSource,), {"_ipif_instance": self})

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
