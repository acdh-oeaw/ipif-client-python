class IPIFClientException(Exception):
    pass


class IPIFClientConfigurationError(IPIFClientException):
    pass


class IPIFClientQueryError(IPIFClientException):
    pass


class IPIFClientDataError(IPIFClientException):
    pass
