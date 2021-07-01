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
# and will try any alternate URIs as well, combining the results
# (if 'hound mode' is on — otherwise, just all the results separately)

# N.B. Persons and Sources are considered 'endpoint-independent', so can be reconciled.
# Factoids and Statements from a particular endpoint are considered unique (in IPIF
# spec, Factoids and Statements do not have a 'uris' property)



# Now access properties of the persons, structured according to the IPIF data model

person.factoids[0].source.id
# => "TheIdOfTheSource"

# Where a result only has *-ref data (i.e. just the @id attribute), it will automatically
# fetch the missing data when it is accessed

person.factoids[0].source.label

```

## Proposed search interface

```python
## SEARCHING (not really implemented yet)

persons = ipif.Person.sourceId("someSourceId")
# Builds a lazy query set that does not access any endpoints until needed

person = persons.first()
# Now we go to the endpoints for data


# Iterating also fetches data
for person in persons:
    print(person)


# IPIF paging is automatically taken care of (page size is the server default or
# a manually configured size)

# (This cannot be done lazily, unless 'hound mode' is off... )


# All the endpoints are hit, the results reconciled, and then we check
# all the other endpoints for alternative URIs for the same person to make
# sure that we have all the Factoids...

person.factoids[0].statements[0].name.label # => 'John'
# And then accessible as above



# Other methods not implemented yet

persons = ipif.Person.sourceId("someSourceId")

persons.count() # => 123

... etc.


# Searching with Statement Parameters

johns = ipif.Person.has_statement(name="John")
# Simple!

johns_from_graz = johns.has_statement(place="Graz")
# Will use IPIF's `independentStatements=true` param to match distinct statements


# Where the multilple statement params need to be grouped according to statement,
# the client will carry out multiple requests, then do a union of the results

persons_graz_c1900 = ipif.Person.has_statement(place="Graz", from_data=1900, to_date=1920)

persons_graz_called_john = persons_graz_c1900.has_statement(name="John")


```