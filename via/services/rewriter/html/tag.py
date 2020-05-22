from html import escape

from via.services.rewriter.ruleset import Attribute


class TagFactory:
    def __init__(self, url_rewriter):
        self._url_rewriter = url_rewriter

    def start(cls, name, attrs):
        return f"<{name}{cls._format_attrs(name, attrs)}>"

    def end(cls, name):
        return f"</{name}>"

    def self_closing(cls, name, attrs):
        return f"<{name}{cls._format_attrs(name, attrs)} />"

    def _format_attrs(self, name, attrs):
        if not attrs:
            return ""

        parts = []
        for key, value in attrs:
            if value is None:
                parts.append(key)
            else:
                if Attribute.is_interesting(name, key):
                    new_value = self._url_rewriter.rewrite(name, key, value)
                    if new_value:
                        value = new_value

                parts.append(f'{key}="{escape(value)}"')

        return " " + " ".join(parts)
