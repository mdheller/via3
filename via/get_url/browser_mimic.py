import json
import random
import re
from collections import OrderedDict, defaultdict
from glob import glob
from os.path import basename

from edit_distance import SequenceMatcher
from Levenshtein import distance
from pkg_resources import resource_filename

from via.get_url import clean_headers
from via.get_url.headers import reorder_headers


class BrowserMimic:
    referer_locations = None
    header_sets = None
    header_fingerprints = None
    user_agents = None

    non_finger_printing_keys = {"Cookie", "Referer", "Host", "DNT"}

    UA_NUMBERS = re.compile(r"\b[0-9._]+\b")

    @classmethod
    def init(cls):
        cls._load_header_sets()
        cls._analyse_header_sets()

    @classmethod
    def random_mimic(cls):
        return random.choice(cls.header_sets.values())

    @classmethod
    def mimic_headers(cls, headers):
        # To avoid detection we must present the headers in the same order we
        # received them

        if "User-Agent" not in headers:
            return cls.random_mimic()

        headers = clean_headers(headers)
        if "Referer" not in headers:
            headers["Referer"] = "http://www.google.com"

        possible_browsers, _, _ = cls.identify_browser(headers)
        if possible_browsers:
            browser_guess = possible_browsers[0]
            headers = reorder_headers(headers, cls.header_sets[browser_guess])

        return headers

    @classmethod
    def identify_browser(cls, headers):
        browsers, score, match_method = [], 0.0, None

        user_agent = headers.get("User-Agent")
        if user_agent:
            match_method = "user-agent"
            browsers, score = cls._nearest_match(
                user_agent, cls.user_agents, comparison_fn=cls._string_match
            )

        if not browsers:
            match_method = "header-set"
            browsers, score = cls._nearest_match(
                cls._header_fingerprint(headers),
                cls.header_fingerprints,
                comparison_fn=cls._collection_match,
            )

        return browsers, score, match_method

    @classmethod
    def _header_fingerprint(cls, headers):
        return tuple(
            sorted(
                key for key in headers.keys() if key not in cls.non_finger_printing_keys
            )
        )

    @staticmethod
    def _string_match(target, comparison):
        dist = distance(target, comparison)
        min_length = min(len(target), len(comparison))

        return 1 - (dist / max(min_length, 1))

    @staticmethod
    def _collection_match(target, comparison):
        diff = SequenceMatcher(a=target, b=comparison)
        return diff.ratio()

    @classmethod
    def _nearest_match(cls, target, pairs, comparison_fn, min_ratio=0.7):
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
    def _load_header_sets(cls):
        cls.header_sets = {}

        for ua_file in glob(resource_filename("via", "resource/header_sets/*.json")):
            with open(ua_file) as handle:
                header_set = OrderedDict(json.load(handle))
                browser_name = basename(ua_file).replace(".json", "")
                cls.header_sets[browser_name] = header_set

    @classmethod
    def _analyse_header_sets(cls):
        header_fingerprints = defaultdict(list)
        user_agents = defaultdict(list)

        for browser_name, header_set in cls.header_sets.items():
            user_agents[header_set.get("User-Agent")].append(browser_name)
            header_fingerprints[cls._header_fingerprint(header_set)].append(
                browser_name
            )

        cls.header_fingerprints = dict(header_fingerprints)
        cls.user_agents = dict(user_agents)


BrowserMimic.init()
