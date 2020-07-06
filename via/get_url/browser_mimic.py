"""Tools for mimicking calls directly from real browsers."""

import json
import random
import re
from collections import OrderedDict, defaultdict
from glob import glob
from os.path import basename

from edit_distance import SequenceMatcher
from Levenshtein import distance
from pkg_resources import resource_filename

from via.get_url.headers import clean_headers, reorder_headers


class BrowserMimic:
    """Toolset for mimicking a browser."""

    # The presence of these headers are so variable they are of no use in
    # finger printing.
    NON_FINGER_PRINTING_HEADERS = {"Cookie", "Referer", "Host", "DNT"}

    UA_NUMBER_PATTERN = re.compile(r"\b[0-9._]+\b")

    _header_sets = None
    _header_fingerprints = None
    _user_agents = None

    @classmethod
    def random_headers(cls):
        """Get a random set of headers captured from a browser.

        :return: An OrderedDict of headers to pass to 3rd parties.
        """
        return random.choice(cls._header_sets.values())

    @classmethod
    def mimic_headers(cls, headers):
        """Convert headers to ones which appear to come from a browser.

        This involves:

         * Cleaning headers modified or added by our tech stack (AWS, NGINX
           etc.)
         * Adding defaults for headers which make them appear to have come from
           natural browsing activity
         * Re-order the headers as they would be received from the browser, if
           they can be matched to a browser.

        If there is no `User-Agent` at all, an example set captured from a
        browser will be returned.

        :return: An OrderedDict of headers to pass to 3rd parties.
        """
        if "User-Agent" not in headers:
            return cls.random_headers()

        headers = clean_headers(headers)
        if "Referer" not in headers:
            headers["Referer"] = "http://www.google.com"

        browser_guess = cls.identify_browser(headers, best_guess=True)
        if browser_guess:
            headers = reorder_headers(headers, cls._header_sets[browser_guess])

        return headers

    @classmethod
    def identify_browser(cls, headers, best_guess=False):
        """Try to match the given browser to our know set.

        :param headers: The headers to match on
        :param best_guess: Get a single value, rather than all equally likely
                           matches
        :return: A single match if `best_guess` is enabled, or a list of
                 equally likely candidates.
        """
        browsers, score, match_method = [], 0.0, None

        user_agent = headers.get("User-Agent")
        if user_agent:
            match_method = "user-agent"
            browsers, score = cls._nearest_match(
                user_agent, cls._user_agents, comparison_fn=cls._string_match
            )

        if not browsers:
            match_method = "header-set"
            browsers, score = cls._nearest_match(
                cls._header_fingerprint(headers),
                cls._header_fingerprints,
                comparison_fn=cls._collection_match,
            )

        if best_guess:
            return browsers[0] if browsers else None

        return browsers, score, match_method

    @classmethod
    def _header_fingerprint(cls, headers):
        return tuple(
            key for key in headers.keys() if key not in cls.NON_FINGER_PRINTING_HEADERS
        )

    @staticmethod
    def _collection_match(target, comparison):
        """Edit distance ratio for arbitrary collections.

        This should not be used for strings (as it's slow).
        """

        diff = SequenceMatcher(a=target, b=comparison)
        return diff.ratio()

    @staticmethod
    def _string_match(target, comparison):
        """Edit distance ratio for strings.

        This should be used for strings as it's much faster than
        _collection_match.
        """
        dist = distance(target, comparison)
        min_length = min(len(target), len(comparison))

        return 1 - (dist / max(min_length, 1))

    @classmethod
    def _nearest_match(cls, target, pairs, comparison_fn, min_ratio=0.7):
        """Get the nearest equal matches under the comparison function.

        Higher values from the comparison function are considered better.
        """
        best_score, best_matches = min_ratio, []

        for comparison, browser_names in pairs.items():
            ratio = comparison_fn(target, comparison)

            if ratio == best_score:
                best_matches.extend(browser_names)

            if ratio > best_score:
                best_score, best_matches = ratio, list(browser_names)

            if ratio == 1.0:
                break

        return best_matches, best_score

    @classmethod
    def _init(cls):
        """Load data and pre-populate required data for comparison."""
        cls._load_header_sets()
        cls._analyse_header_sets()

    @classmethod
    def _load_header_sets(cls):
        """Read from JSON data."""
        cls._header_sets = {}

        for ua_file in glob(resource_filename("via", "resource/_header_sets/*.json")):
            with open(ua_file) as handle:
                header_set = OrderedDict(json.load(handle))
                browser_name = basename(ua_file).replace(".json", "")
                cls._header_sets[browser_name] = header_set

    @classmethod
    def _analyse_header_sets(cls):
        """Create look-ups for different kinds of matching."""
        header_fingerprints = defaultdict(list)
        user_agents = defaultdict(list)

        for browser_name, header_set in cls._header_sets.items():
            user_agents[header_set.get("User-Agent")].append(browser_name)
            header_fingerprints[cls._header_fingerprint(header_set)].append(
                browser_name
            )

        cls._header_fingerprints = dict(header_fingerprints)
        cls._user_agents = dict(user_agents)


# Load static data
BrowserMimic._init()
