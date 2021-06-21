ipif-client-python
==================

A Python client for [IPIF](https://github.com/GVogeler/prosopogrAPhI) prosopography API endpoints. 


Client API so far:

```python


from ipif_client import IPIF

# Initialise a new client
ipif = IPIF()

# Add some IPIF endpoints
ipif.add_endpoint(name="APIS", uri="http://apis.oeaw.ac.at/ipif/")
ipif.add_endpoint(name="SomeOther", uri="http://something.net/ipif/")

# Each IPIF client instance keeps its own data, backends etc., and instantiates
# its own IPIF-entity classes

ipif.Factoids
ipif.Persons
ipif.Statements
ipif.Sources


# Look up Person with a particular ID

person = ipif.Persons.id("someId")

# IPIF client will search *all* the endpoints for person.id=someId
# and will try any alternate URIs successfully returned 

```