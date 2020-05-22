import requests
from pyramid.httpexceptions import HTTPConflict, HTTPNotFound
from requests.exceptions import RequestException

from via.services.timeit import timeit


class Document:
    def __init__(self, document_url):
        self.url = document_url
        self.original = None
        self.content = None

    def get_original(self, headers, expect_type=None, timeout=10, stream=False):
        user_agent = headers.get("User-Agent")

        print("Requesting URL:", self.url, headers)

        with timeit("retrieve content"):
            try:
                original = requests.get(
                    self.url,
                    # Pass the user agent
                    headers={"User-Agent": user_agent},
                    timeout=timeout,
                    stream=stream,
                )
            except RequestException as err:
                raise HTTPConflict(f"Cannot get '{self.url}' with error: {err}")

        if expect_type:
            content_type = original.headers["Content-Type"]
            if not content_type or expect_type not in content_type:
                raise HTTPNotFound(
                    f"No content of type '{expect_type}' found: got {content_type}"
                )

        self.original = original
        if stream:
            self.content = None
        else:
            self.content = original.content

    def update_response(self, response):
        """Add relevant settings from the original request."""
        response.content_type = self.original.headers["Content-Type"]

        return response
