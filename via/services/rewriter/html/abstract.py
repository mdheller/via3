import os
from html import escape

from jinja2 import Environment, PackageLoader, select_autoescape

from via.services.rewriter.interface import AbstractRewriter


class AbstractHTMLRewriter(AbstractRewriter):
    # Things our children do
    inject_client = True

    def __init__(self, url_rewriter, h_config):
        """
        :param static_url: The base URL for our transparent proxying
        """
        super().__init__(url_rewriter)

        self._h_config = h_config
        self._jinja_env = Environment(
            loader=PackageLoader("via", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _get_client_embed(self):
        template = self._jinja_env.get_template("client_inject.js.jinja2")

        return template.render(
            h_embed_url=os.environ.get("H_EMBED_URL", "https://hypothes.is/embed.js"),
            hypothesis_config=self._h_config,
        )

    def get_page_inserts(self, doc_url):
        if not self.inject_client:
            return {}

        # base_url = self.url_rewriter.rewrite_html(doc_url)
        embed = self._get_client_embed()

        return {
            # "head_top": f'\n<link rel="canonical" href="{escape(doc_url)}">\n<base href="{escape(base_url)}">\n',
            "head_top": f'\n<link rel="canonical" href="{escape(doc_url)}">\n<base href="{escape(doc_url)}">\n',
            "head_bottom": f'\n<script type="text/javascript">{embed}</script>\n',
        }
