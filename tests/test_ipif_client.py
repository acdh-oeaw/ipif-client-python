import pytest

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
        ipif.add_endpoint(label="something")
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(uri=URI)

    # Check endpoints dict is there
    assert ipif._endpoints == {}

    # Test adding an endpoint
    ipif.add_endpoint("APIS", uri=URI)
    assert ipif._endpoints["APIS"] == URI

    # Test duplicate label causes exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(label="APIS", uri=URI)

    # Test duplicate uri causes exception
    with pytest.raises(IPIFClientConfigurationError):
        ipif.add_endpoint(label="somethingElse", uri=URI)


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

    ipif.add_endpoint(label="APIS", uri=URI)

    assert ipif.Person._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Source._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Statement._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Factoid._ipif_instance._endpoints["APIS"] == URI
