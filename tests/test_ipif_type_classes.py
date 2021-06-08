from ipif_client.ipif import IPIF

from .test_data import TEST_PERSON_RESPONSE, TEST_SOURCE_RESPONSE, TEST_FACTOID_RESPONSE


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


"""
def test_thing():
    ipif = IPIF()

    p = ipif.Persons._init_from_id_json({"@id": "something"})

    assert p.label == "GO GET FROM SERVER"
"""
