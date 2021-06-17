import pytest
import requests
import time

from ipif_client import __version__

from ipif_client.ipif import (
    IPIF,
    IPIFClientDataError,
    IPIFQuerySet,
    IPIFClientConfigurationError,
    IPIFClientQueryError,
)

from .test_data import (
    TEST_FACTOID_RESPONSE,
    TEST_PERSON_RESPONSE,
    TEST_PERSON_SEARCH_RESPONSE,
    TEST_STATEMENT_RESPONSE,
)

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
    assert ipif.Persons

    assert ipif.Persons._ipif_instance is ipif

    assert ipif.Sources._ipif_instance is ipif
    assert ipif.Statements._ipif_instance is ipif
    assert ipif.Factoids._ipif_instance is ipif

    ipif.add_endpoint(name="APIS", uri=URI)

    assert ipif.Persons._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Sources._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Statements._ipif_instance._endpoints["APIS"] == URI
    assert ipif.Factoids._ipif_instance._endpoints["APIS"] == URI


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


def test_doing_id_request_from_ipif_type(httpserver):
    httpserver.expect_request(
        f"/persons/{TEST_PERSON_RESPONSE['@id']}"
    ).respond_with_json(TEST_PERSON_RESPONSE)

    ipif = IPIF()
    ipif.add_endpoint("TEST", uri=httpserver.url_for("/"))

    ipif.Persons.id(TEST_PERSON_RESPONSE["@id"])
    print(ipif._data_cache)
    assert (
        ipif.Persons._ipif_instance._data_cache[
            ("TEST", "persons", TEST_PERSON_RESPONSE["@id"])
        ]["@id"]
        == TEST_PERSON_RESPONSE["@id"]
    )


def test_search_queries_return_queryset_of_right_type():
    ipif = IPIF()

    qs = ipif.Persons.factoidId("someFactoidId")

    assert isinstance(qs, IPIFQuerySet)
    assert isinstance(qs, ipif._PersonsQuerySet)
    assert qs.__class__.__name__ == "PersonsQuerySet"


def test_queryset_methods_return_queryset():
    ipif = IPIF()

    qs = ipif._PersonsQuerySet()

    assert isinstance(qs, ipif._PersonsQuerySet)

    qs2 = qs.factoidId("someFactoidId")

    assert isinstance(qs, ipif._PersonsQuerySet)

    assert qs2._search_params == {"factoidId": "someFactoidId"}

    qs3 = qs2.f("someFactoidSearchTerm")
    assert qs3._search_params == {
        "factoidId": "someFactoidId",
        "f": "someFactoidSearchTerm",
    }


def test_id_functions_raise_error_on_own_class():
    ipif = IPIF()

    with pytest.raises(IPIFClientQueryError):
        ipif._PersonsQuerySet().personId("something")

    with pytest.raises(IPIFClientQueryError):
        ipif._StatementsQuerySet().statementId("something")

    with pytest.raises(IPIFClientQueryError):
        ipif.Persons.personId("something")


def test_id_function_uses_cache_if_possible(mocker):
    ipif = IPIF()
    ipif.add_endpoint("TEST", uri="http://test")

    requester = mocker.spy(requests, "get")

    ipif._data_cache[
        ("TEST", "persons", TEST_PERSON_RESPONSE["@id"])
    ] = TEST_PERSON_RESPONSE

    ipif.Persons.id(TEST_PERSON_RESPONSE["@id"])

    assert requester.call_count == 0

    ipif.Persons.id("SomethingNotFoundBefore")

    assert requester.call_count == 1


def test_id_function_returns_a_factoid_or_statement():
    ipif = IPIF()

    ipif.add_endpoint("WORKS", "http://works/")
    ipif.add_endpoint("OTHER", "http://other/")
    ipif.add_endpoint("FAILS", "http://fails")

    ipif._data_cache[
        ("WORKS", "factoids", "factoid__39986__original_source_3994")
    ] = TEST_FACTOID_RESPONSE

    ipif._data_cache[
        ("OTHER", "factoids", "factoid__39986__original_source_3994")
    ] = None
    ipif._data_cache[("FAILS", "factoids", "factoid__39986__original_source_3994")] = {
        "IPIF_STATUS": "Request failed"
    }

    f = ipif.Factoids.id("factoid__39986__original_source_3994")
    assert f
    assert f.id == "WORKS::factoid__39986__original_source_3994"

    ipif._data_cache[
        ("WORKS", "statements", "39986_PersonInstitution_95989")
    ] = TEST_STATEMENT_RESPONSE
    ipif._data_cache[("OTHER", "factoids", "39986_PersonInstitution_95989")] = None
    ipif._data_cache[("FAILS", "factoids", "39986_PersonInstitution_95989")] = {
        "IPIF_STATUS": "Request failed"
    }

    st = ipif.Statements.id("39986_PersonInstitution_95989")
    assert st
    assert st.id == "WORKS::39986_PersonInstitution_95989"


def test_id_function_with_factoid_or_statement_two_matches():
    ipif = IPIF()

    ipif.add_endpoint("WORKS", "http://works")
    ipif.add_endpoint("ALSO_WORKS", "http://also_works")

    ipif._data_cache[
        ("WORKS", "factoids", "factoid__39986__original_source_3994")
    ] = TEST_FACTOID_RESPONSE
    ipif._data_cache[
        ("ALSO_WORKS", "factoids", "factoid__39986__original_source_3994")
    ] = TEST_FACTOID_RESPONSE

    with pytest.raises(IPIFClientDataError):
        ipif.Factoids.id("factoid__39986__original_source_3994")


def test_simple_reconcile_persons_from_id():
    ipif = IPIF()
    ipif._preferred_endpoint = "ENDPOINT_B"
    ipif.add_endpoint("ENDPOINT_A", "http://a")
    ipif.add_endpoint("ENDPOINT_B", "http://b")

    PERSON_RESPONSE_A = {
        "@id": "http://a/39986",
        "label": "Schneller, István (39986)",
        "createdBy": "None",
        "createdWhen": "2016-10-03T20:53:28+00:00Z",
        "modifiedBy": "None",
        "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
        "uris": ["http://d-nb.info/gnd/1031597824"],
        "factoid-refs": [
            {
                "@id": "THE_A_FACTOIDS",
                "statement-refs": [
                    {"@id": "AN_A_STATEMENT"},
                    {"@id": "ANOTHER_A_STATEMENT"},
                ],
                "source-ref": {"@id": "THE_A_SOURCE"},
                "person-ref": {"@id": "39986"},
            }
        ],
    }

    PERSON_RESPONSE_B = {
        "@id": "some_B_resp",
        "label": "Schneller, István (39986)",
        "createdBy": "None",
        "createdWhen": "2014-10-03T20:53:28+00:00Z",
        "modifiedBy": "None",
        "modifiedWhen": "2014-10-03T20:53:28+00:00Z",
        "uris": ["http://a/39986"],
        "factoid-refs": [
            {
                "@id": "THE_B_FACTOIDS",
                "statement-refs": [
                    {"@id": "THE_B_STATEMENT"},
                    {"@id": "ANOTHER_B_STATEMENT"},
                ],
                "source-ref": {"@id": "THE_B_SOURCE"},
                "person-ref": {"@id": "39986"},
            }
        ],
    }

    endpoint_name, p_dict = ipif.Persons._reconcile_persons_from_id(
        {
            "ENDPOINT_A": PERSON_RESPONSE_A,
            "ENDPOINT_B": PERSON_RESPONSE_B,
        }
    )

    assert p_dict

    assert p_dict["factoid-refs"] == [
        {
            "@id": "THE_B_FACTOIDS",
            "statement-refs": [
                {"@id": "THE_B_STATEMENT"},
                {"@id": "ANOTHER_B_STATEMENT"},
            ],
            "source-ref": {"@id": "THE_B_SOURCE"},
            "person-ref": {"@id": "39986"},
            "ipif-endpoint": "ENDPOINT_B",
        },
        {
            "@id": "THE_A_FACTOIDS",
            "statement-refs": [
                {"@id": "AN_A_STATEMENT"},
                {"@id": "ANOTHER_A_STATEMENT"},
            ],
            "source-ref": {"@id": "THE_A_SOURCE"},
            "person-ref": {"@id": "39986"},
            "ipif-endpoint": "ENDPOINT_A",
        },
    ]

    # We call set in the function, which potentially throws the order
    assert set(p_dict["uris"]) == set(
        ["http://a/39986", "http://d-nb.info/gnd/1031597824"]
    )


def test_reconcile_persons_from_id_with_extra_hounding(mocker):
    ipif = IPIF()
    ipif._preferred_endpoint = "ENDPOINT_A"
    ipif.add_endpoint("ENDPOINT_A", "http://a")
    ipif.add_endpoint("ENDPOINT_B", "http://b")

    PERSON_RESPONSE_A = {
        "@id": "http://a/39986",
        "label": "Schneller, István (39986)",
        "createdBy": "None",
        "createdWhen": "2016-10-03T20:53:28+00:00Z",
        "modifiedBy": "None",
        "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
        "uris": ["http://d-nb.info/gnd/1031597824"],
        "factoid-refs": [
            {
                "@id": "THE_A_FACTOIDS",
                "statement-refs": [
                    {"@id": "AN_A_STATEMENT"},
                    {"@id": "ANOTHER_A_STATEMENT"},
                ],
                "source-ref": {"@id": "THE_A_SOURCE"},
                "person-ref": {"@id": "39986"},
            }
        ],
    }

    PERSON_RESPONSE_B = {
        "@id": "http://d-nb.info/gnd/1031597824",
        "label": "Schneller, István (39986)",
        "createdBy": "None",
        "createdWhen": "2014-10-03T20:53:28+00:00Z",
        "modifiedBy": "None",
        "modifiedWhen": "2014-10-03T20:53:28+00:00Z",
        "uris": ["http://a/39986"],
        "factoid-refs": [
            {
                "@id": "THE_B_FACTOIDS",
                "statement-refs": [
                    {"@id": "THE_B_STATEMENT"},
                    {"@id": "ANOTHER_B_STATEMENT"},
                ],
                "source-ref": {"@id": "THE_B_SOURCE"},
                "person-ref": {"@id": "39986"},
            }
        ],
    }

    ipif._data_cache[
        ("ENDPOINT_B", "persons", "http://d-nb.info/gnd/1031597824")
    ] = PERSON_RESPONSE_B

    requester = mocker.spy(IPIF, "_request_single_object_by_id")

    p_endpoint_name, p_dict = ipif.Persons._reconcile_persons_from_id(
        {"ENDPOINT_A": PERSON_RESPONSE_A, "ENDPOINT_B": None}
    )

    assert requester.call_count == 1

    assert len(p_dict["factoid-refs"]) == 2
    assert p_dict["factoid-refs"] == [
        {
            "@id": "THE_A_FACTOIDS",
            "statement-refs": [
                {"@id": "AN_A_STATEMENT"},
                {"@id": "ANOTHER_A_STATEMENT"},
            ],
            "source-ref": {"@id": "THE_A_SOURCE"},
            "person-ref": {"@id": "39986"},
            "ipif-endpoint": "ENDPOINT_A",
        },
        {
            "@id": "THE_B_FACTOIDS",
            "statement-refs": [
                {"@id": "THE_B_STATEMENT"},
                {"@id": "ANOTHER_B_STATEMENT"},
            ],
            "source-ref": {"@id": "THE_B_SOURCE"},
            "person-ref": {"@id": "39986"},
            "ipif-endpoint": "ENDPOINT_B",
        },
    ]


def test_ipif_client_base_query_request(httpserver):
    httpserver.expect_request("/persons").respond_with_json(TEST_PERSON_SEARCH_RESPONSE)

    ipif = IPIF()
    ipif.add_endpoint(name="APIS", uri=httpserver.url_for("/"))

    resp = ipif._base_query_request("APIS", "Persons", {"sourceId": "someSource"})
    assert resp == TEST_PERSON_SEARCH_RESPONSE


def fake_iterated_response(totalHits, size, page):

    is_last_page = not (totalHits % (page * size) < totalHits)
    if is_last_page:
        return {
            "protocol": {
                "size": totalHits % (size),
                "totalHits": totalHits,
                "page": page,
            },
            "persons": [
                {"@id": f"ID_{n}"}
                for n in range(
                    (page - 1) * size + 1, (page - 1) * size + totalHits % (size) + 1
                )
            ],
        }
    return {
        "protocol": {"size": size, "totalHits": totalHits, "page": page},
        "persons": [
            {"@id": f"ID_{n}"}
            for n in range((page - 1) * size + 1, (page - 1) * size + size + 1)
        ],
    }


def test_fake_iterated_response():
    assert fake_iterated_response(27, 10, 1) == {
        "protocol": {"size": 10, "totalHits": 27, "page": 1},
        "persons": [
            {"@id": "ID_1"},
            {"@id": "ID_2"},
            {"@id": "ID_3"},
            {"@id": "ID_4"},
            {"@id": "ID_5"},
            {"@id": "ID_6"},
            {"@id": "ID_7"},
            {"@id": "ID_8"},
            {"@id": "ID_9"},
            {"@id": "ID_10"},
        ],
    }

    assert fake_iterated_response(27, 10, 2) == {
        "protocol": {"size": 10, "totalHits": 27, "page": 2},
        "persons": [
            {"@id": "ID_11"},
            {"@id": "ID_12"},
            {"@id": "ID_13"},
            {"@id": "ID_14"},
            {"@id": "ID_15"},
            {"@id": "ID_16"},
            {"@id": "ID_17"},
            {"@id": "ID_18"},
            {"@id": "ID_19"},
            {"@id": "ID_20"},
        ],
    }

    assert fake_iterated_response(27, 10, 3) == {
        "protocol": {"size": 7, "totalHits": 27, "page": 3},
        "persons": [
            {"@id": "ID_21"},
            {"@id": "ID_22"},
            {"@id": "ID_23"},
            {"@id": "ID_24"},
            {"@id": "ID_25"},
            {"@id": "ID_26"},
            {"@id": "ID_27"},
        ],
    }


def yield_responses(responses):
    for r in responses:
        for p in r["persons"]:
            yield p


def test_ipif_client_iterate_results_from_single_endpoint(httpserver):
    responses = [
        fake_iterated_response(100, 30, 1),
        fake_iterated_response(100, 30, 2),
        fake_iterated_response(100, 30, 3),
        fake_iterated_response(100, 30, 3),
    ]

    for i in range(4):
        httpserver.expect_request(
            "/persons",
            query_string={"sourceId": "someSourceId", "page": str(i + 1), "size": "30"},
        ).respond_with_json(responses[i])

    # Sanity
    assert (
        requests.get(
            httpserver.url_for("/persons"),
            params={"sourceId": "someSourceId", "page": "1", "size": "30"},
        ).json()
        == responses[0]
    )

    ipif = IPIF()
    ipif.add_endpoint("APIS", uri=httpserver.url_for("/"))

    results_iterator = ipif._iterate_results_from_single_endpoint(
        "APIS", "Persons", {"sourceId": "someSourceId"}
    )

    # Finally, test that results_iterator produces a list of persons
    for expected, resp in zip(yield_responses(responses), results_iterator):
        assert expected == resp


def no_time_out(t):
    """Patch timeout_wrapper with a short time for testing"""
    time.sleep(0.0001)


def test_ipif_client_iterate_results_from_single_endpoint_with_error(
    httpserver, mocker
):
    ipif = IPIF()
    ipif.add_endpoint(name="NONESUCH", uri="http://no")

    results_iterator = ipif._iterate_results_from_single_endpoint(
        "NONESUCH", "Persons", {"sourceId": "someSourceId"}
    )

    # Patch timeout_wrapper to avoid waiting a second between retries
    mocker.patch("ipif_client.ipif.timeout_wrapper", new=no_time_out)

    assert list(results_iterator) == [{"IPIF_STATUS": "Request failed"}]


"""
def test_query_request_from_endpoints(httpserver):
    httpserver.expect_request()
"""

"""
Logic of URI 'hounding'
=======================

- get some results from all the endpoints...
- go through results and get IDs that have returned null from 




NB:
persons and sources are independent of IPIF, so can be equated across endpoints
factoids/statements can just flat contradict each other


"""
