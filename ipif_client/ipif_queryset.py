from .exceptions import IPIFClientQueryError


class IPIFQuerySet:
    def __init__(self, search_params=None, *args, **kwargs):
        self._search_params = search_params or {}
        self._data = []

    def _spawn_new_with_search_param(param: str):
        """Takes name of a parameter and returns function
        which creates a new instance of IPIFQuerySet with its param=arg
        accumulated"""

        def inner_func(self, value):
            class_name = self.__class__.__name__.replace("sQuerySet", "")
            if param == class_name.lower() + "Id":
                raise IPIFClientQueryError(f"")

            return self.__class__(
                search_params={
                    **self._search_params,
                    param: value,
                }
            )

        return inner_func

    factoidId = _spawn_new_with_search_param("factoidId")
    f = _spawn_new_with_search_param("f")
    sourceId = _spawn_new_with_search_param("sourceId")
    s = _spawn_new_with_search_param("s")
    statementId = _spawn_new_with_search_param("statementId")
    st = _spawn_new_with_search_param("st")
    personId = _spawn_new_with_search_param("personId")
    p = _spawn_new_with_search_param("p")

    @staticmethod
    def _merge_results_set(data_dict):
        pass

    @staticmethod
    def _trivially_merge(data_dict):
        ## UNDERACHIEVERS MUST TRY HARDER

        results_list = []
        for endpoint_name, result_list in data_dict.items():
            print(result_list)
            results_list += result_list

        return results_list

    def _with_data(func):
        """Method decorator to get data as required before
        calling the desired function."""

        def inner(self, *args, **kwargs):
            if not self._data:
                self._data = self._trivially_merge(
                    self._ipif_instance._query_request_from_endpoints(
                        "PERSONS", self._search_params
                    )
                )
            return func(self, *args, **kwargs)

        return inner

    @_with_data
    def __iter__(self):
        yield from self._data

    @_with_data
    def first(self):
        pass

    @_with_data
    def __getitem__(self, n):

        return self._data[n]
