class AbstractRewriter:
    streaming = False

    def __init__(self, url_rewriter):
        self.url_rewriter = url_rewriter

    def rewrite(self, doc):
        raise NotImplementedError()
