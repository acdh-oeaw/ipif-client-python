import pytest
import requests

from ipif_client import __version__

from ipif_client.ipif import IPIF, IPIFClientConfigurationError

URI = "http://some-ipif-endpoint.com/ipif/"


def test_version():
    assert __version__ == "0.1.0"


def test_ipif_init_with_no_config():
    ipif = IPIF()


def test_add_endpoint():
    ipif = IPIF()

    # Test adding some nonsense raises exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint("something")

    # Missing one or other arg also raises exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(name="something")
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(uri=URI)

    # Check endpoints dict is there
    assert ipif._endpoints == {}

    # Test adding an endpoint
    ipif.add_endpoint("APIS", uri=URI)
    assert ipif._endpoints["APIS"] == URI

    # Test duplicate label causes exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(name="APIS", uri=URI)

    # Test duplicate uri causes exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(name="somethingElse", uri=URI)


def test_ipif_init_with_endpoint_config():
    ipif = IPIF(
        {
            "endpoints": {
                "APIS": URI,
                "other": "http://something-different.net",
            },
        },
    )

    assert ipif._endpoints["APIS"] == URI
    assert ipif._endpoints["other"] == "http://something-different.net"


def test_ipif_initialises_with_ipif_type_classes():
    ipif = IPIF()
    assert ipif.Person

    assert ipif.Person._ipif_instance is ipif

    assert ipif.Source._ipif_instance is ipif
    assert ipif.Statement._ipif_instance is ipif
    assert ipif.Factoid._ipif_instance is ipif

    ipif.add_endpoint(name="APIS", uri=URI)

    assert ipif.Person._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Source._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Statement._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Factoid._ipif_instance._endpoints["APIS"] == URI


def test_http_server_mock(httpserver):
    httpserver.expect_request("/foobar").respond_with_json({"foo": "bar"})
    # check that the request is served
    assert requests.get(httpserver.url_for("/foobar")).json() == {"foo": "bar"}


def test_error_if_no_endpoints_decorator():
    ipif = IPIF()

    with pytest.raises(IPIFClientConfigurationError):
        ipif._request_single_object_by_id("APIS", "person", "the_id")

    ipif.add_endpoint(name="APIS", uri=URI)


def test_request_single_object_by_id(httpserver):

    httpserver.expect_request("/persons/anIdString").respond_with_json(
        {"@id": "anIdString"}
    )

    ipif = IPIF()
    ipif.add_endpoint("TEST", uri=httpserver.url_for("/"))

    # Test we get a result as planned
    assert ipif._request_single_object_by_id("TEST", "Persons", "anIdString") == {
        "@id": "anIdString"
    }

    httpserver.expect_request("/persons/MISSING").respond_with_data(
        "Not found", status=404
    )

    # Test we get a None if the request 404's
    assert ipif._request_single_object_by_id("TEST", "Persons", "MISSING") == None

    # Otherwise, set a result status of Failed
    assert ipif._request_single_object_by_id("TEST", "Persons", "ARSE") == {
        "IPIF_STATUS": "Request failed"
    }


def test_request_id_from_endpoints(httpserver):

    httpserver.expect_request("/succeed/persons/anIdString").respond_with_json(
        {"@id": "anIdString"}
    )
    httpserver.expect_request("/notFound/persons/anIdString").respond_with_data(
        "Not found", status=404
    )

    ipif = IPIF()
    ipif.add_endpoint("TEST_SUCCEED", uri=httpserver.url_for("/succeed/"))
    ipif.add_endpoint("TEST_NOT_FOUND", uri=httpserver.url_for("/notFound/"))
    ipif.add_endpoint("TEST_NOSERVER", uri="http://not_there.net")

    result = ipif._request_id_from_endpoints("Persons", "anIdString")
    assert result["TEST_SUCCEED"] == {"@id": "anIdString"}
    assert result["TEST_NOSERVER"] == {"IPIF_STATUS": "Request failed"}
    assert "TEST_NOT_FOUND" not in result
