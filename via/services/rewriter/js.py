import copy
import re

from via.services.rewriter.interface import AbstractRewriter


def _replace_identifier(js_source, identifier, replacement):
    # Crude regex to find references to the identifier. This will also end
    # up matching the identifier if it occurs in comments, string or regex
    # literals.
    #
    # A more sophisticated implementation of this function might use an
    # ECMAScript lexer to tokenize the source and only check identifiers for
    # matches.
    return re.sub(r"\b" + identifier + r"\b", replacement, js_source)


class JSRewriter(AbstractRewriter):
    QUOTED_URL_REGEX = re.compile(r"[\"'](https?://[^\"']+)[\"']", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("utf-8")

        replacements = []

        for match in self.QUOTED_URL_REGEX.finditer(content):
            url = match.group(1)
            print("JS FIND!", url)

            quotes = ""

            if url.startswith('"') or url.startswith("'"):
                quotes = url[0]
                url = url.strip("\"'")

            new_url = self.url_rewriter.rewrite(
                tag="external-js", attribute=None, url=url
            )
            if not new_url:
                continue

            if new_url != url:
                print("REPLACE!", url, ">>", new_url)
                # replacements.append((match.group(0), f"url({quotes}{new_url}{quotes})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        # Replace references to `location` (the global variable), `document.location` or
        # `window.location` with a custom property which refers to the proxied URL
        # rather than the real URL. We can't do this with monkey-patching on
        # the client alone because `location` is an "unforgeable" property.
        #
        # This will replace references to other identifiers that happen to be called
        # `location` as well, but in most cases that won't break anything as long
        # as all references are treated the same way.
        content = _replace_identifier(content, "location", "viaLocation")

        # Strip sourcemap URLs. The original source maps will no longer be
        # applicable following changes to the content.
        content = re.sub(r"//# sourceMappingURL=.*$", "//", content)

        return content
