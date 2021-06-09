TEST_PERSON_RESPONSE = {
    "@id": "39986",
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


TEST_SOURCE_RESPONSE = {
    "@id": "original_source_3994",
    "label": "Original source  3994",
    "uris": ["/apis/api/metainfo/source/3994/"],
    "createdBy": "None",
    "createdWhen": "2016-10-03T20:53:28Z",
    "modifiedWhen": "2016-10-03T20:53:28Z",
    "factoid-refs": [
        {
            "@id": "factoid__39986__original_source_3994",
            "statement-refs": [
                {"@id": "39986_PersonInstitution_95989"},
                {"@id": "39986_PersonInstitution_95994"},
                {"@id": "39986_PersonInstitution_96001"},
                {"@id": "39986_PersonInstitution_96006"},
            ],
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
        }
    ],
}


TEST_FACTOID_RESPONSE = {
    "@id": "factoid__39986__original_source_3994",
    "createdBy": "None",
    "createdWhen": "2016-10-03T20:53:28+00:00Z",
    "modifiedBy": "None",
    "modifiedWhen": "2016-10-03T20:53:28+00:00Z",
    "source-ref": {"@id": "original_source_3994"},
    "statement-refs": [
        {"@id": "39986_PersonInstitution_95989"},
        {"@id": "39986_PersonInstitution_95994"},
        {"@id": "39986_PersonInstitution_96001"},
        {"@id": "39986_PersonPlace_97169"},
        {"@id": "39986_PersonPlace_97170"},
        {"@id": "39986_PersonPlace_97171"},
        {"@id": "39986_attrb_name"},
        {"@id": "39986_attrb_start_date"},
        {"@id": "39986_attrb_end_date"},
        {"@id": "39986_attrb_first_name"},
        {"@id": "39986_attrb_gender"},
        {"@id": "39986_m2m_profession_141"},
        {"@id": "39986_m2m_profession_149"},
        {"@id": "39986_m2m_profession_2268"},
    ],
    "person-ref": {"@id": "39986"},
}


TEST_STATEMENT_RESPONSE = {
    "@id": "39986_PersonInstitution_95989",
    "statementType": {"label": "relatedToInstitution"},
    "name": "Lebowski, Lebowski",
    "memberOf": {
        "uri": [
            "http://d-nb.info/gnd/10353110-5",
            "/apis/entities/entity/institution/95465/detail",
        ],
        "label": "Evang. Lyzeum (Sopron)",
    },
    "role": {"label": "war Student"},
    "date": {
        "label": "1866-01-01-1868-01-01",
        "sortdate": "1866-01-01T00:00:00Z",
    },
    # Added fake person to make this a "complete" example
    "relatesToPersons": [
        {
            "uris": [
                "http://names-online.madeup/dude",
            ],
            "label": "The Dude",
        }
    ],
    "places": [
        {
            "uris": [
                "http://sws.geonames.org/3049366/",
                "/apis/entities/entity/place/6090/detail",
            ],
            "label": "Köszeg",
        }
    ],
    "statementText": "Schneller, István (war Student) Evang. Lyzeum (Sopron)",
    "createdBy": "MKaiser",
    "createdWhen": "2016-09-21T12:09:26+00:00Z",
    "modifiedBy": "MKaiser",
    "modifiedWhen": "2016-09-21T12:09:26+00:00Z",
    "factoid-refs": [
        {
            "@id": "factoid__39986__original_source_3994",
            "source-ref": {"@id": "original_source_3994"},
            "person-ref": {"@id": "39986"},
            "statement-refs": [
                {"@id": "39986_PersonInstitution_95989"},
                {"@id": "39986_PersonInstitution_95994"},
                {"@id": "39986_PersonInstitution_96001"},
                {"@id": "39986_PersonInstitution_96006"},
                {"@id": "39986_PersonInstitution_96007"},
                {"@id": "39986_PersonInstitution_96008"},
                {"@id": "39986_PersonInstitution_96011"},
                {"@id": "39986_PersonPlace_39987"},
                {"@id": "39986_PersonPlace_39988"},
                {"@id": "39986_PersonPlace_95987"},
                {"@id": "39986_PersonPlace_95988"},
                {"@id": "39986_PersonPlace_95990"},
                {"@id": "39986_PersonPlace_95991"},
                {"@id": "39986_PersonPlace_96002"},
                {"@id": "39986_PersonPlace_96003"},
                {"@id": "39986_PersonPlace_96004"},
                {"@id": "39986_PersonPlace_96005"},
                {"@id": "39986_PersonPlace_97169"},
                {"@id": "39986_PersonPlace_97170"},
                {"@id": "39986_PersonPlace_97171"},
                {"@id": "39986_attrb_name"},
                {"@id": "39986_attrb_start_date"},
                {"@id": "39986_attrb_end_date"},
                {"@id": "39986_attrb_first_name"},
                {"@id": "39986_attrb_gender"},
                {"@id": "39986_m2m_profession_141"},
                {"@id": "39986_m2m_profession_149"},
                {"@id": "39986_m2m_profession_2268"},
            ],
        }
    ],
}
