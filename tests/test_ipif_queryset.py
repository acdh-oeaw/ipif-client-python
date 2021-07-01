from ipif_client import IPIF

P1 = {
    "@id": "http://APIS/39986",
    "label": "Schneller, István (39986)",
    "createdBy": "None",
    "createdWhen": "2016-10-03T20:53:28+00:00Z",
    "modifiedBy": "None",
    "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
    "uris": ["http://d-nb.info/gnd/1031597824"],
    "factoid-refs": [
        {
            "@id": "factoid__39986__original_source_3994",
            "statement-refs": [
                {"@id": "39986_PersonInstitution_95989"},
                {"@id": "39986_PersonInstitution_95994"},
            ],
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
        }
    ],
}

P2 = {
    "@id": "OTHER_VERSION_OF_P1",
    "label": "Istvan Schneller",
    "createdBy": "None",
    "createdWhen": "2016-10-03T20:53:28+00:00Z",
    "modifiedBy": "None",
    "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
    "uris": ["http://d-nb.info/gnd/1031597824", "http://APIS/39986"],
    "factoid-refs": [
        {
            "@id": "anotherFactoidId",
            "statement-refs": [
                {"@id": "anotherStatementId1"},
                {"@id": "anotherStatementId2"},
            ],
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
        }
    ],
}

P3 = {
    "@id": "COMPLETELY_DIFFERENT_ONE",
    "label": "Other Dude",
    "createdBy": "None",
    "createdWhen": "2016-10-03T20:53:28+00:00Z",
    "modifiedBy": "None",
    "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
    "uris": [],
    "factoid-refs": [
        {
            "@id": "NothingToDoWithItFactoid",
            "statement-refs": [
                {"@id": "nothingToDoWithIt1"},
                {"@id": "nothingToDoWithIt2"},
            ],
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
        }
    ],
}


def test_queryset_merge_persons():

    DATA = {"endpointA": [], "endpointB": []}

    ipif = IPIF()
    qs = ipif._PersonsQuerySet()

    qs._merge_results_set(DATA)
