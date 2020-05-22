from collections import deque

from lxml.html import HTMLParser

from via.services.rewriter.html.abstract import AbstractHTMLRewriter
from via.services.rewriter.html.tag import TagFactory
from via.services.timeit import timeit


class ParserCallback:
    def __init__(self, tag_factory, inserts):
        self.buffer = deque()
        self.tag_factory = tag_factory
        self.inserts = inserts

    def start(self, tag, attrib):
        self.buffer.append(self.tag_factory.start(tag, attrib.items()))

        if tag == "head":
            self.buffer.append(self.inserts.get("head_top", ""))

    def end(self, tag):
        if tag == "head":
            self.buffer.append(self.inserts.get("head_bottom", ""))

        self.buffer.append(self.tag_factory.end(tag))

    def data(self, data):
        self.buffer.append(data)

    def comment(self, text):
        self.buffer.append(f"<!-- {text} -->")

    def close(self):
        pass


class LXMLStreamingRewriter(AbstractHTMLRewriter):
    streaming = True

    def rewrite(self, doc):
        callback = ParserCallback(
            TagFactory(self.url_rewriter), inserts=self.get_page_inserts(doc.url)
        )
        parser = HTMLParser(target=callback)

        lines_written = 0
        lines_read = 0

        with timeit("streaming HTML rewrite time"):
            # TODO! How are you supposed to get the real one?
            yield b"<!DOCTYPE html>\n"

            for line in doc.original.iter_lines():
                lines_read += 1

                parser.feed(line)
                while callback.buffer:
                    lines_written += 1
                    yield callback.buffer.popleft().encode("utf-8")

            while callback.buffer:
                lines_written += 1
                yield callback.buffer.popleft().encode("utf-8")

        print(f"LXML STREAMED: lines {lines_read} read / {lines_written} written")
