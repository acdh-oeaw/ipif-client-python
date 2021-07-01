import datetime
from ipif_client.ipif import IPIF
from ipif_client.ipif_entity_types import Statements

from .test_data import (
    TEST_PERSON_RESPONSE,
    TEST_SOURCE_RESPONSE,
    TEST_FACTOID_RESPONSE,
    TEST_STATEMENT_RESPONSE,
)


def test_create_person_from_init_json():
    ipif = IPIF()

    p = ipif.Persons._init_from_id_json(TEST_PERSON_RESPONSE, endpoint_name="APIS")

    assert type(p).__name__ == "Person"
    assert isinstance(p, ipif.Persons)
    assert p.local_id == "39986"
    assert p["@id"] == "39986"

    assert p.label == "Schneller, István (39986)"
    assert str(p) == "Person: Schneller, István (39986)"

    assert p.uris == ["http://d-nb.info/gnd/1031597824"]

    assert len(p.factoids) == 1
    assert p.factoids[0].id == "factoid__39986__original_source_3994"

    assert isinstance(p.factoids[0].source, ipif.Sources)
    assert isinstance(p.factoids[0].statements[0], ipif.Statements)


def test_create_source_from_init_json():
    ipif = IPIF()

    s = ipif.Sources._init_from_id_json(TEST_SOURCE_RESPONSE, endpoint_name="APIS")

    assert type(s).__name__ == "Source"
    assert isinstance(s, ipif.Sources)
    assert s.local_id == "original_source_3994"
    assert s["@id"] == "original_source_3994"

    assert s.label == "Original source  3994"
    assert str(s) == "Source: Original source  3994"

    assert s.uris == ["/apis/api/metainfo/source/3994/"]

    assert len(s.factoids) == 1
    assert s.factoids[0].id == "factoid__39986__original_source_3994"

    assert isinstance(s.factoids[0].source, ipif.Sources)
    assert isinstance(s.factoids[0].statements[0], ipif.Statements)


def test_create_factoid_from_init_json():
    ipif = IPIF()

    f = ipif.Factoids._init_from_id_json(TEST_FACTOID_RESPONSE, endpoint_name="APIS")
    assert type(f).__name__ == "Factoid"
    assert isinstance(f, ipif.Factoids)
    assert f.local_id == "factoid__39986__original_source_3994"
    assert f["@id"] == "factoid__39986__original_source_3994"
    assert isinstance(f.source, ipif.Sources)
    assert f.source.id == "original_source_3994"
    assert isinstance(f.person, ipif.Persons)
    assert f.person.id == "39986"

    assert len(f.statements) == 14
    for statement in f.statements:
        assert isinstance(statement, ipif.Statements)


def test_create_statement_from_init_json():
    ipif = IPIF()

    st = ipif.Statements._init_from_id_json(
        TEST_STATEMENT_RESPONSE, endpoint_name="APIS"
    )
    assert isinstance(st, ipif.Statements)
    assert st.local_id == "39986_PersonInstitution_95989"
    assert st["@id"] == "39986_PersonInstitution_95989"
    assert len(st.factoids) == 1
    assert st.factoids[0].id == "factoid__39986__original_source_3994"

    assert st.createdBy == "MKaiser"
    assert st.modifiedBy == "MKaiser"

    assert isinstance(st.factoids[0].source, ipif.Sources)
    assert st.factoids[0].source.id == "original_source_3994"
    assert isinstance(st.factoids[0].statements[0], ipif.Statements)
    assert st.factoids[0].statements[0].id == "39986_PersonInstitution_95989"
    assert isinstance(st.factoids[0].person, ipif.Persons)
    assert st.factoids[0].person.id == "39986"

    assert st.statementType.label == "relatedToInstitution"
    assert st.name == "Lebowski, Lebowski"
    assert st.memberOf.label == "Evang. Lyzeum (Sopron)"
    assert st.memberOf.uri == [
        "http://d-nb.info/gnd/10353110-5",
        "/apis/entities/entity/institution/95465/detail",
    ]
    assert st.role.label == "war Student"
    assert st.date.label == "1866-01-01-1868-01-01"
    assert st.date.sortdate == datetime.datetime(1866, 1, 1)
    assert st.statementText == "Schneller, István (war Student) Evang. Lyzeum (Sopron)"
    assert st.places[0].uris == [
        "http://sws.geonames.org/3049366/",
        "/apis/entities/entity/place/6090/detail",
    ]
    assert st.places[0].label == "Köszeg"
    assert st.relatesToPersons[0].uris == [
        "http://names-online.madeup/dude",
    ]
    assert st.relatesToPersons[0].label == "The Dude"


def test_create_factoid_from_factoid_ref_json():
    ipif = IPIF()

    f = ipif.Factoids._init_from_ref_json(
        {
            "@id": "factoid__39986__original_source_3994",
            "statement-refs": [
                {"@id": "39986_PersonInstitution_95989"},
                {"@id": "39986_PersonInstitution_95994"},
            ],
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
        }
    )

    assert f.id == "factoid__39986__original_source_3994"
    assert len(f.statements) == 2
    assert isinstance(f.statements[0], ipif.Statements)

    assert isinstance(f.source, ipif.Sources)


def test_ipif_type_gets_full_item_when_accessed():
    ipif = IPIF()

    ipif.add_endpoint("TEST", "http://test/")

    ipif._data_cache[
        ("TEST", "factoids", TEST_FACTOID_RESPONSE["@id"])
    ] = TEST_FACTOID_RESPONSE

    ipif._data_cache[
        ("TEST", "statements", "39986_PersonInstitution_95989")
    ] = TEST_STATEMENT_RESPONSE
    # 39986_PersonInstitution_95989 is the ID of TEST_STATEMENT_RESPONSE

    f = ipif.Factoids.id(TEST_FACTOID_RESPONSE["@id"])

    assert f.id == "TEST::factoid__39986__original_source_3994"

    assert f.statements[0].id == "39986_PersonInstitution_95989"

    st = f.statements[0]

    assert st._ref_only == True

    assert st.name == "Lebowski, Lebowski"

    assert st._ref_only == False


{
    "@id": "27527_PersonEvent_141805",
    "statementType": {"label": "relatedToEvent"},
    "role": {"label": "stellte aus"},
    "date": {"label": ["None"]},
    "statementText": "Tangl, Karlmann (stellte aus) Ordered Pizza",
    "createdBy": "rhadden",
    "createdWhen": "2021-01-13T10:47:20.853031+00:00Z",
    "modifiedBy": "rhadden",
    "modifiedWhen": "2021-01-13T10:47:20.853031+00:00Z",
    "factoid-refs": [
        {
            "@id": "factoid__27527__original_source_594",
            "source-ref": {"@id": "original_source_594"},
            "person-ref": {"@id": 27527},
            "statement-refs": [
                {"@id": "27527_PersonEvent_141805"},
                {"@id": "27527_PersonInstitution_96043"},
                {"@id": "27527_PersonInstitution_96047"},
                {"@id": "27527_PersonInstitution_96054"},
                {"@id": "27527_PersonInstitution_96060"},
                {"@id": "27527_PersonInstitution_96064"},
                {"@id": "27527_PersonInstitution_96065"},
                {"@id": "27527_PersonInstitution_96066"},
                {"@id": "27527_PersonInstitution_96068"},
                {"@id": "27527_PersonInstitution_96069"},
                {"@id": "27527_PersonInstitution_96071"},
                {"@id": "27527_PersonInstitution_96072"},
                {"@id": "27527_PersonInstitution_96073"},
                {"@id": "27527_PersonInstitution_96074"},
                {"@id": "27527_PersonInstitution_96076"},
                {"@id": "27527_PersonInstitution_96079"},
                {"@id": "27527_PersonInstitution_96080"},
                {"@id": "27527_PersonInstitution_96081"},
                {"@id": "27527_PersonInstitution_96087"},
                {"@id": "27527_PersonInstitution_96091"},
                {"@id": "27527_PersonInstitution_96097"},
                {"@id": "27527_PersonInstitution_96099"},
                {"@id": "27527_PersonInstitution_96100"},
                {"@id": "27527_PersonInstitution_96101"},
                {"@id": "27527_PersonInstitution_96102"},
                {"@id": "27527_PersonInstitution_141788"},
                {"@id": "27527_PersonPlace_27528"},
                {"@id": "27527_PersonPlace_27529"},
                {"@id": "27527_PersonPlace_96032"},
                {"@id": "27527_PersonPlace_96044"},
                {"@id": "27527_PersonPlace_96050"},
                {"@id": "27527_PersonPlace_96051"},
                {"@id": "27527_PersonPlace_96055"},
                {"@id": "27527_PersonPlace_96056"},
                {"@id": "27527_PersonPlace_96061"},
                {"@id": "27527_PersonPlace_96067"},
                {"@id": "27527_PersonPlace_96070"},
                {"@id": "27527_PersonPlace_96075"},
                {"@id": "27527_PersonPlace_96083"},
                {"@id": "27527_PersonPlace_96084"},
                {"@id": "27527_PersonPlace_141642"},
                {"@id": "27527_PersonPlace_141779"},
                {"@id": "27527__PersonPerson_5411__96031"},
                {"@id": "27527__PersonPerson_5742__141801"},
                {"@id": "27527_attrb_name"},
                {"@id": "27527_attrb_start_date"},
                {"@id": "27527_attrb_end_date"},
                {"@id": "27527_attrb_first_name"},
                {"@id": "27527_attrb_gender"},
                {"@id": "27527_m2m_profession_149"},
                {"@id": "27527_m2m_profession_188"},
                {"@id": "27527_m2m_profession_713"},
            ],
        }
    ],
}
