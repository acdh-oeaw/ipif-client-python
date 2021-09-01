from multilookupdict import MultiLookupDict

DATA = {
    "a": [
        {
            "@id": "a1",
            "uris": [
                "b1",
            ],
            "factoid-refs": ["a1Data1", "a1Data2"],
        },
        {
            "@id": "a2",
            "uris": [],
            "factoid-refs": ["a2Data1", "a2Data2"],
        },
    ],
    "b": [
        {
            "@id": "b1",
            "uris": [],
            "factoid-refs": ["b1Data1", "b1Data2"],
        },
        {
            "@id": "b2",
            "uris": [],
            "factoid-refs": ["b2Data1", "b2Data2"],
        },
    ],
    "c": [
        {
            "@id": "c1",
            "uris": [],
            "factoid-refs": ["c1Data1"],
        },
        {
            "@id": "c2",
            "uris": [],
            "factoid-refs": ["c2Data1", "c2Data2", "c2Data3"],
        },
    ],
}


def merge(item, matching_item):
    new_item = {**item}
    new_item["factoid-refs"] += matching_item["factoid-refs"]
    new_item["uris"] += matching_item["uris"]

    return new_item


res = MultiLookupDict()

for endpoint_name, data in DATA.items():
    for item in data:

        # Get current item's identifiers
        item_identifiers = [item["@id"], *item["uris"]]

        existing_enitites = res[item_identifiers]

        if existing_enitites:
            # Here, update existing (n.b. we know, because existing_entities is not empty
            # that one of the item["@id"] or item["uris"] must already exist in the MLD)
            res[tuple([item["@id"], *item["uris"]])] = merge(
                res[existing_enitites[0]["@id"]], item
            )

        else:
            res[tuple([item["@id"], *item["uris"]])] = item


print(res.keys())
print(res)
