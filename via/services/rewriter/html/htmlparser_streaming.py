from collections import deque
from html.parser import HTMLParser
from io import StringIO

from via.services.rewriter.html.abstract import AbstractHTMLRewriter
from via.services.rewriter.html.tag import TagFactory
from via.services.timeit import timeit


class StreamingParser(HTMLParser):
    def __init__(self, tag_factory, inserts):
        super().__init__(convert_charrefs=False)

        self.buffer = deque()
        self.inserts = inserts
        self.tag_factory = tag_factory
        self.handle = StringIO()

    def _write(self, data):
        self.buffer.append(data)

    def handle_starttag(self, tag, attrs):
        self._write(self.tag_factory.start(tag, attrs))

        if tag == "head":
            self._write(self.inserts.get("head_top", ""))

    def handle_endtag(self, tag):
        if tag == "body":
            self._write(self.inserts.get("head_bottom", ""))

        self._write(self.tag_factory.end(tag))

    def handle_startendtag(self, tag, attrs):
        self._write(self.tag_factory.self_closing(tag, attrs))

    def handle_data(self, data):
        # Raw content
        self._write(data)

    def handle_comment(self, data):
        self._write(f"<!-- {data} -->")

    def handle_decl(self, decl):
        self._write(f"<!{decl}>")

    def handle_pi(self, data):
        self._write(f"<{data}>")

    def unknown_decl(self, data):
        self._write(f"<![{data}]>")

    def handle_entityref(self, name):
        self._write(f"&{name};")

    def handle_charref(self, name):
        self._write(f"&#{name};")


class HTMLParserRewriter(AbstractHTMLRewriter):
    streaming = True

    def rewrite(self, doc):
        parser = StreamingParser(
            TagFactory(self.url_rewriter), self.get_page_inserts(doc.url)
        )

        with timeit("parse html"):
            for line in doc.original.iter_lines():
                parser.feed(line.decode("utf-8"))

            while parser.buffer:
                yield parser.buffer.popleft().encode("utf-8")

            while parser.buffer:
                yield parser.buffer.popleft().encode("utf-8")

            parser.close()
