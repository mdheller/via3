import re

from via.services.rewriter.interface import AbstractRewriter


class CSSRewriter(AbstractRewriter):
    URL_REGEX = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("utf-8", errors="replace")

        replacements = []

        for match in self.URL_REGEX.finditer(content):
            url = match.group(1)

            quotes = ""

            if url.startswith('"') or url.startswith("'"):
                quotes = url[0]
                url = url.strip("\"'")

            new_url = self.url_rewriter.rewrite(
                tag="external-css", attribute=None, url=url
            )
            if not new_url:
                continue

            if new_url != url:
                replacements.append((match.group(0), f"url({quotes}{new_url}{quotes})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        # Strip sourcemap URLs. The original source maps will no longer be
        # applicable following changes to the content.
        content = re.sub(r"/\*# sourceMappingURL=.*\*/", "", content, flags=re.MULTILINE)

        return content
