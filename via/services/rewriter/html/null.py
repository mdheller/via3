from via.services.rewriter.html.abstract import AbstractHTMLRewriter


class NullRewriter(AbstractHTMLRewriter):
    def rewrite(self, doc):
        return doc.content.decode("utf-8")
