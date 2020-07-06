"""Methods for working with headers."""

from collections import OrderedDict

# A mix of headers we don't want to pass on for one reason or another
BANNED_HEADERS = {
    # Requests needs to set Host to the right thing for us
    "Host",
    # Don't pass Cookies
    "Cookie",
    # AWS things
    "X-Amzn-Trace-Id",
    # AWS NGINX / NGINX things
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

# Something get incorrectly Title-cased by the stack by the time they've got to
# us. If we pass them on like this could mark us out as a bot.
HEADER_MAP = {"Dnt": "DNT"}

# Some values need to be faked or fixed
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


def clean_headers(headers):
    """Remove Cloudflare and other cruft from the headers.

    This will attempt to present a clean version of the headers which can be
    used to make a request to the 3rd party site.

    Also:

      * Map the headers as if we had come from a Google Search
      * Remove things added by AWS and Cloudflare etc.
      * Fix some header names

    This is intended to return a list of headers that can be passed on to the
    upstream service.

    :param headers: A mapping of header values
    :return: An OrderedDict of cleaned headers
    """
    clean = OrderedDict()

    for header_name, value in headers.items():
        if header_name in BANNED_HEADERS:
            continue

        # Map to standard names for things
        header_name = HEADER_MAP.get(header_name, header_name)

        # Add in defaults for certain fields
        value = HEADER_DEFAULTS.get(header_name, value)

        clean[header_name] = value

    return clean


def reorder_headers(target, exemplar):
    """Re-order the headers in the target to match an exemplar.

    All fields in the exemplar will be re-ordered to match. Those not in the
    exemplar will be left in place.

    :return: An OrderedDict of headers
    """

    result = OrderedDict()
    for key in _sort_list_by_exemplar(list(target.keys()), list(exemplar.keys())):
        result[key] = target[key]

    return result


def _sort_list_by_exemplar(target, exemplar):
    result = [None] * len(target)
    sortable_keys = []
    available_indexes = []

    for index, key in enumerate(target):
        if key in exemplar:
            # The exemplar has an opinion on ordering, so this position is
            # available to be ordered, but we don't know which key will get it
            sortable_keys.append(key)
            available_indexes.append(index)
        else:
            # If it's not in the exemplar, we have no information about where
            # to put it, so just put it back in place
            result[index] = key

    # All the sortable keys should be re-ordered into their exemplar order
    sortable_keys.sort(key=exemplar.index)

    # Then we can slot them back into the available indexes
    for key, index in zip(sortable_keys, available_indexes):
        result[index] = key

    return result
