class IPIF:
    def __init__(self, conf_dict):
        pass
        self.backends = []

    def add_backend(self, URL):
        self.backends.append(URL)

    class Persons:
        @classmethod
        def id(cls, id):
            pass

        @classmethod
        def source(cls, url):
            pass

        @classmethod
        def filter_by_statement(cls, *args, **kwargs):
            pass


ipif = IPIF(
    {
        "backends": {
            "APIS": "http://apis-ipif.at/ipif",
        },
    }
)

ipif.add_backend(label="APIS", uri="http://apis-ipif.at/ipif")


ipif.Persons.id("some_id_string")  # => returns Persons instance or None

ipif.Persons.source(
    "http://something.net/theDude"
)  # => returns list of Persons instances

ipif.Persons.factoidId()

ipif.Persons.filter_by_statement(
    name="John", fromDate=1901, toDate="asdf"
)  # returns PersonsQuerySet, resolves to list of Persons


# Search params
"""
size
page
sortBy
p
factoidId
f
statementId
st
sourceId
s
"""

# Statement params
"""
statementText
relatesToPerson
memberOf
role
name
from
to
place
"""
