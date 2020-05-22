from via.services.rewriter.html.htmlparser import HTMLParserRewriter
from via.services.rewriter.html.lxml import LXMLRewriter
from via.services.rewriter.html.null import NullRewriter

HTML_REWRITERS = {
    "htmlparser": HTMLParserRewriter,
    "lxml": LXMLRewriter,
    "null": NullRewriter,
    None: LXMLRewriter,
}
