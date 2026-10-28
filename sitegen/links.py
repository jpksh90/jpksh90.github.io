"""Checking that local links and #fragments in generated pages resolve."""

from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit


class LinkCollector(HTMLParser):
    """Collect the href/src targets and the element ids of a page."""

    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])
        if tag == "base":
            return
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])


def parse_page(path, cache):
    """Return the LinkCollector for `path`, parsing it at most once."""
    key = path.resolve()
    if key not in cache:
        cache[key] = LinkCollector()
        cache[key].feed(path.read_text())
    return cache[key]


def broken_links(output_dir, html_paths):
    """Return 'page: link (reason)' for local links that do not resolve.

    A link is broken if its file is missing or empty, or if its #fragment
    names no element on the target page.
    """
    problems = []
    parsed = {}
    for html_path in html_paths:
        for link in parse_page(html_path, parsed).links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue  # external or mailto:
            target = html_path  # a bare "#fragment" points at this page
            if parts.path:
                target = output_dir / unquote(parts.path).lstrip("/")
                if parts.path.endswith("/"):
                    target = target / "index.html"
                if not target.is_file():
                    problems.append(f"{html_path.name}: {link} (missing)")
                    continue
                if target.stat().st_size <= 1:
                    problems.append(f"{html_path.name}: {link} (empty file)")
                    continue
            fragment = unquote(parts.fragment)
            # "#top" always scrolls to the top, even without a matching id.
            if (
                fragment
                and fragment.lower() != "top"
                and target.suffix == ".html"
                and fragment not in parse_page(target, parsed).ids
            ):
                problems.append(
                    f"{html_path.name}: {link} (no #{fragment} on {target.name})"
                )
    return problems
