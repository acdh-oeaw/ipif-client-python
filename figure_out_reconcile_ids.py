SERVER_ENDPOINTS = {
    "SE": ["balls"],
    "S1": ["TJones"],
    "S2": ["TJones", "JonesT", "T_JONES"],
    "S3": ["T_JONES"],
}


def get_from_endpoint(endpoint, id_string):
    if id_string in SERVER_ENDPOINTS[endpoint]:
        return SERVER_ENDPOINTS[endpoint]
    else:
        return None


## Algorithm here
endpoints = set(SERVER_ENDPOINTS.keys())


def do_getting(ids_to_try=set(), endpoints=set(), accumulated_ids=set()):

    unresolved_endpoints = set(endpoints)

    start_id = ids_to_try.pop()

    print("---")
    for ep in endpoints:

        ids = get_from_endpoint(ep, start_id)
        print("getting", ep, "returns", ids)
        if ids:
            for id in ids:
                accumulated_ids.add(id)
            unresolved_endpoints.remove(ep)
            for id in ids:
                ids_to_try.add(id)

    ids_to_try.remove(start_id)
    print("UR", unresolved_endpoints)
    print("AC_ID", accumulated_ids)
    print("IDS_TO_TRY", ids_to_try)

    if unresolved_endpoints and ids_to_try:
        return do_getting(
            ids_to_try=ids_to_try,
            endpoints=unresolved_endpoints,
            accumulated_ids=accumulated_ids,
        )
    else:
        return accumulated_ids


res = do_getting(ids_to_try={"JonesT"}, endpoints=endpoints, accumulated_ids=set())
print("=====")
print(res)
