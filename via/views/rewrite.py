from pyramid import view
from pyramid.response import Response

from via.services.document import Document
from via.services.rewriter import RewriterService
from via.services.timeit import timeit


@view.view_config(
    route_name="view_css", http_cache=0,
)
def view_css(context, request):
    return _rewrite(
        context,
        request,
        expect_type="text/css",
        rewrite_provider=RewriterService(context, request).get_css_rewriter,
        timeout=3,
    )


@view.view_config(
    route_name="view_js", http_cache=0,
)
def view_js(context, request):
    return _rewrite(
        context,
        request,
        expect_type="javascript",
        rewrite_provider=RewriterService(context, request).get_js_rewriter,
        timeout=3,
    )


@view.view_config(
    route_name="view_html", http_cache=0,
)
def view_html(context, request):
    return _rewrite(
        context,
        request,
        expect_type="text/html",
        rewrite_provider=RewriterService(context, request).get_html_rewriter,
    )


def _rewrite(context, request, expect_type, rewrite_provider, timeout=10):
    print("------------------------------")
    document_url = context.url()
    rewriter = rewrite_provider(document_url)

    doc = Document(document_url)
    doc.get_original(
        headers=request.headers,
        expect_type=expect_type,
        timeout=timeout,
        stream=rewriter.streaming,
    )

    response = Response()
    doc.update_response(response)

    if rewriter.streaming:
        # We can't get a timing here because it happens elsewhere
        response.app_iter = rewriter.rewrite(doc)
        return response

    with timeit(f"{expect_type} rewriting total"):
        doc.content = rewriter.rewrite(doc)

    response.body = doc.content.encode("utf-8")

    return response
