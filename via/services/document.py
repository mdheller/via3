from urllib.parse import urlparse

import requests
from pyramid.httpexceptions import HTTPConflict, HTTPNotFound
from requests.exceptions import RequestException

from via.services.timeit import timeit


class Document:
    def __init__(self, document_url, verify_ssl=True):
        self.url = document_url
        self.original = None
        self.content = None
        self.verify_ssl = verify_ssl

    def get_original(
        self, headers, cookies, expect_type=None, timeout=10, stream=False
    ):
        user_agent = headers.get("User-Agent")

        print("Requesting URL:", self.url, headers)
        print("\tCookies:", cookies)

        with timeit("retrieve content"):
            try:
                original = requests.get(
                    self.url,
                    # Pass the user agent
                    headers={"User-Agent": user_agent},
                    timeout=timeout,
                    stream=stream,
                    verify=self.verify_ssl,
                    cookies=cookies,
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

        url_parts = urlparse(self.url)
        cookie_path = "/".join(["/html", url_parts.scheme, url_parts.hostname])

        for cookie in self.original.cookies:
            print(cookie)

            response.set_cookie(
                name=cookie.name,
                value=cookie.value,
                # max_age=cookie.max_age,
                path=cookie_path,
                # domain='localhost:9083',
                secure=cookie.secure,
                expires=cookie.expires,
                # httponly=cookie.httponly,
                comment=cookie.comment,
                # samesite=cookie.samesite,
            )

        return response
