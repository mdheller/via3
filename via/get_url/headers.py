"""Methods for working with headers."""

from collections import OrderedDict

BANNED_HEADERS = {
    # Requests needs to set Host to the right thing for us
    "Host",
    # AWS things
    "X-Amzn-Trace-Id",
    # AWS NGINX things
    "X-Forwarded-Server",
    "X-Forwarded-For",
    "X-Real-Ip",
    "X-Forwarded-Proto",
    "X-Forwarded-Port",
    "X-Request-Start",
    # Cloudflare things
    "Cf-Request-Id",
    "Cf-Connecting-Ip",
    "Cf-Ipcountry",
    "Cf-Ray",
    "Cf-Visitor",
    "Cdn-Loop",
}

HEADER_MAP = {"Dnt": "DNT"}

HEADER_DEFAULTS = {
    # Mimic what it looks like if you got here from a Google search
    "Referer": "https://www.google.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    # This gets overwritten by AWS NGINX
    "Connection": "keep-alive",
}


def clean_headers(headers, pass_cookies=False):
    """Remove Cloudflare and other cruft from the headers.

    Also:

      * Map the headers as if we had come from a Google Search
      * Remove things added by AWS and Cloudflare etc.
      * Fix some header names

    This is intended to return a list of headers that can be passed on to the
    upstream service.

    :param headers: A mapping of header values
    :param pass_cookies: Allow cookies through
    :return: An OrderedDict of cleaned headers
    """
    clean = OrderedDict()

    for header_name, value in headers.items():
        if header_name in BANNED_HEADERS:
            continue

        if header_name == "Cookie" and not pass_cookies:
            continue

        # Map to standard names for things
        header_name = HEADER_MAP.get(header_name, header_name)

        # Add in defaults for certain fields
        value = HEADER_DEFAULTS.get(header_name, value)

        clean[header_name] = value

    return clean


def reorder_headers(target, exemplar):
    """Re-order the headers in the target to match an exemplar.

    All fields in the exemplar will come first, other fields will appear in the
    same order they were found at the end of the set of headers.

    :return: An OrderedDict of headers
    """

    target_keys = list(target.keys())
    exemplar_keys = list(exemplar.keys())
    in_exemplar = set(target_keys) & set(exemplar_keys)

    def sort_value(key):
        if key in in_exemplar:
            return 0, exemplar_keys.index(key)

        return 1, target_keys.index(key)

    sorted_headers = OrderedDict()
    for key in sorted(target_keys, key=sort_value):
        sorted_headers[key] = target[key]

    return sorted_headers
