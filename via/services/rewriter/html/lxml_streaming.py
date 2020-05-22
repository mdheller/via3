from lxml.html import HTMLParser

from via.services.rewriter.html.abstract import AbstractHTMLRewriter
from via.services.rewriter.html.tag import TagFactory


class ParserCallback:
    def __init__(self, tag_factory, inserts, buffer):
        self.buffer = buffer

        # TODO! How are you supposed to get the real one?
        buffer.add("<!DOCTYPE html>\n")

        self._tag_factory = tag_factory
        self._inserts = inserts

    def start(self, tag, attrib):
        self.buffer.add(self._tag_factory.start(tag, attrib))

        if tag == "head":
            self.buffer.add(self._inserts.get("head_top", ""))

    def end(self, tag):
        if tag == "head":
            self.buffer.add(self._inserts.get("head_bottom", ""))

        self.buffer.add(self._tag_factory.end(tag))

    def data(self, data):
        self.buffer.add(data)

    def comment(self, text):
        self.buffer.add(f"<!-- {text} -->")

    def close(self):
        pass


class LXMLStreamingRewriter(AbstractHTMLRewriter):
    streaming = True

    def _get_streaming_parser(self, doc, buffer):
        return HTMLParser(
            target=ParserCallback(
                tag_factory=TagFactory(self.url_rewriter),
                inserts=self.get_page_inserts(doc.url),
                buffer=buffer,
            )
        )
