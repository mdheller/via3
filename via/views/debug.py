"""Views for debugging."""

import json
from collections import OrderedDict
from datetime import datetime

from pyramid import view
from pyramid.response import Response

from via.get_url import clean_headers
from via.get_url.browser_mimic import BrowserMimic


@view.view_config(route_name="debug_headers")
def debug_headers(_context, request):
    """Dump the headers as we receive them for debugging."""

    if request.GET.get("raw"):
        headers = OrderedDict(request.headers)
    else:
        headers = clean_headers(request.headers)

    start = datetime.utcnow()
    looks_like, match_quality, matched_on = BrowserMimic.identify_browser(headers)
    diff = datetime.utcnow() - start
    ms = diff.seconds * 1000 + diff.microseconds / 1000

    mimic_headers = BrowserMimic.mimic_headers(request.headers)

    return Response(
        body=f"""
            <h1>Instructions</h1>
            <ol>
                <li>Access the service directly (not thru *.hypothes.is)
                <li>Enable Do-Not-Track if supported</li>
                <li>
                    <a href="{request.route_url('debug_headers')}">
                        Click here to get referer
                    </a>
                </li>
                <li>Press F5 to get 'Cache-Control'</li>
            </ol>
            
            <a href="{request.route_url('debug_headers')}?raw=1">Show all headers</a>

            Looks like: {looks_like}: {match_quality*100}% (Matched {matched_on} in {ms}ms)
            <hr>
            <h1>Headers received</h1>
            <pre>{json.dumps(headers, indent=4)}</pre><br>

            <hr>
            <h2>Mimicked headers</h2>
            <pre>{json.dumps(mimic_headers, indent=4)}</pre><br>
        """,
        status=200,
    )
