from ipif_client.ipif import IPIF

from .test_data import TEST_PERSON_RESPONSE


def test_create_person_from_init_json():
    ipif = IPIF()

    p = ipif.Persons._init_from_id_json(TEST_PERSON_RESPONSE)

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

    assert f.local_id == "factoid__39986__original_source_3994"
    assert len(f.statements) == 2
    assert isinstance(f.statements[0], ipif.Statements)

    assert isinstance(f.source, ipif.Sources)


def test_thing():
    ipif = IPIF()

    p = ipif.Persons._init_from_id_json({"@id": "something"})

    assert p.label == "GO GET FROM SERVER"
