from via.services.rewriter.html.htmlparser_streaming import HTMLParserRewriter
from via.services.rewriter.html.lxml import LXMLRewriter
from via.services.rewriter.html.lxml_streaming import LXMLStreamingRewriter
from via.services.rewriter.html.null import NullRewriter

HTML_REWRITERS = {
    "htmlparser": HTMLParserRewriter,
    "lxml": LXMLRewriter,
    "lxml_stream": LXMLStreamingRewriter,
    "null": NullRewriter,
    None: LXMLRewriter,
}
