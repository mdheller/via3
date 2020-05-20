from lxml import etree
from lxml.html import document_fromstring, tostring

from via.services.rewriter.core import HTMLRewriter
from via.services.rewriter.img_source_set import ImageSourceSet
from via.services.timeit import timeit


class LXMLRewriter(HTMLRewriter):
    def rewrite(self, doc):
        with timeit("parse html"):
            html_doc = document_fromstring(doc.content)

        with timeit("rewriting"):
            self._rewrite_links(html_doc, doc.url)

            if self.inject_client:
                self._inject_client(html_doc, doc.url)

        with timeit("stringification"):
            # TODO! - Get the original doctype
            return (b"<!DOCTYPE html>" + tostring(html_doc, encoding="utf-8")).decode(
                "utf-8"
            )

    def _inject_client(self, doc, doc_url):
        head = doc.find("head")
        if head is None:
            # We should probably add one in this case
            raise ValueError("No head to inject into!")

        # Let H know where the real document is
        canonical_link = etree.Element(
            "link", attrib={"rel": "canonical", "href": doc_url}
        )
        head.insert(0, canonical_link)

        # Also set the base to try and catch relative links that escape us
        base = etree.Element("base", {"href": self._html_url_fn(doc_url)})
        head.insert(0, base)

        # Inject the script contents
        script_tag = etree.Element("script", attrib={"type": "text/javascript"})
        script_tag.text = self._get_client_embed()
        head.append(script_tag)

    def _rewrite_links(self, doc, doc_url):
        for element, attribute, url, pos in self._iter_links(doc):
            if element.tag == 'img' and attribute == 'srcset':
                self._rewrite_img_srcset(element, doc_url)
                continue

            replacement = self.rewrite_url(
                element.tag, attribute, url, doc_url)
            if replacement is None:
                continue

            if attribute:
                element.set(attribute, replacement)
                continue

            # If there's no attribute, this means we're being asked to rewrite
            # the content of a tag not an attribute
            end = pos + len(url)
            element.text = element.text[:pos] + replacement + element.text[end:]

    def _iter_links(self, doc):
        # This yields (element, attribute, url, pos)
        yield from doc.iterlinks()

        # Lets do the same for things iterlinks doesn't find
        for img in doc.xpath("//img"):
            data_src = img.attrib.get("data-src")
            if data_src:
                yield img, 'data-src', data_src, None

            src_set = img.attrib.get("srcset")
            if src_set:
                yield img, 'srcset', src_set, None

    def _rewrite_img_srcset(self, img, doc_url):
        src_set = img.attrib.get("srcset")
        if not src_set:
            return

        img.attrib["srcset"] = str(ImageSourceSet(src_set).map(
            lambda url: self.rewrite_url('img', 'srcset', url, doc_url)
        ))