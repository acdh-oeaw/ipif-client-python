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
