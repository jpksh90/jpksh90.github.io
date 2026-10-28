import argparse
import functools
import json
import os
import re
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import mistune
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
UPDATES_MARKER = "<!-- UPDATES -->"
UPDATES_WINDOW_MONTHS = 3
# Rendered like the other pages, but kept out of the nav and sitemap.
NOT_FOUND_PAGE = "404"
# Written into every generated page so `clean` only deletes our own output.
GENERATOR = "site-utils.py"
GENERATED_FILES = ("sitemap.xml", "robots.txt")

CONFIG_DEFAULTS = {
    "title": "My Personal Website",
    "email": "",
    "heading": "",
    "url": "",
    "job_title": "",
    "affiliation": "",
    "links": {},
    "pages": {},
    "descriptions": {},
    "photo_credit": "",
    "photo_path": "images/headshot.jpg",
}


def normalize_public_path(path):
    """Return an asset path relative to the published docs root."""
    normalized = os.path.normpath(path).replace("\\", "/")
    if normalized.startswith("../docs/"):
        return normalized[len("../docs/"):]
    if normalized.startswith("docs/"):
        return normalized[len("docs/"):]
    return normalized


def load_config(path=ROOT / "config.yaml"):
    """Load config.yaml on top of the defaults."""
    with open(path) as f:
        config = {**CONFIG_DEFAULTS, **(yaml.safe_load(f) or {})}
    config["url"] = config["url"].rstrip("/")
    config["photo_path"] = normalize_public_path(config["photo_path"])
    return config


def page_url(config, page):
    """Return the absolute URL of a page; the home page maps to the site root."""
    if page == "index":
        return f"{config['url']}/"
    return f"{config['url']}/{page}.html"


def person_json_ld(config):
    """Return schema.org Person data so search engines can link the profiles."""
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": config["heading"],
        "url": page_url(config, "index"),
        "image": f"{config['url']}/{config['photo_path']}",
        "jobTitle": config["job_title"],
        "worksFor": {
            "@type": "CollegeOrUniversity",
            "name": config["affiliation"],
        },
        "email": f"mailto:{config['email']}",
        "sameAs": list(config["links"].values()),
    }
    # Escape "</" so the JSON cannot close the surrounding <script> tag.
    return json.dumps(person, indent=2, ensure_ascii=False).replace("</", "<\\/")


def slugify(text):
    """Turn heading HTML into an id: 'Research &amp; Talks' -> 'research-talks'."""
    plain = unescape(re.sub(r"<[^>]+>", "", text)).lower()
    return re.sub(r"[^\w]+", "-", plain).strip("-")


class AnchoredRenderer(mistune.HTMLRenderer):
    """Markdown renderer that gives every heading a unique id to link to."""

    def __init__(self):
        super().__init__(escape=False)
        self.used_ids = set()

    def heading(self, text, level, **attrs):
        base = slugify(text) or "section"
        anchor, n = base, 2
        while anchor in self.used_ids:
            anchor, n = f"{base}-{n}", n + 1
        self.used_ids.add(anchor)
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'


def write_sitemap(config, output_dir):
    """Write sitemap.xml and robots.txt listing every generated page."""
    entries = "\n".join(
        f"  <url><loc>{page_url(config, page)}</loc></url>"
        for page in config["pages"]
    )
    (output_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n"
    )
    (output_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {config['url']}/sitemap.xml\n"
    )
    print("\tWriting sitemap.xml and robots.txt")


def parse_updates(path):
    """Parse a 'YYYY-MM-DD | text' updates log. Raises on any malformed line."""
    updates = []
    if not os.path.exists(path):
        return updates
    with open(path) as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" not in line:
                raise ValueError(
                    f"{path}:{lineno}: expected 'YYYY-MM-DD | text', got: {line!r}"
                )
            date_str, text = line.split("|", 1)
            date_str = date_str.strip()
            text = text.strip()
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError as e:
                raise ValueError(
                    f"{path}:{lineno}: invalid date {date_str!r} (expected YYYY-MM-DD)"
                ) from e
            if not text:
                raise ValueError(f"{path}:{lineno}: entry has no text")
            updates.append((entry_date, text))
    return updates


def months_ago(months, today=None):
    """Return the date `months` calendar months before `today`."""
    today = today or date.today()
    month = today.month - months
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    day = today.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1


def render_updates(updates, months=UPDATES_WINDOW_MONTHS):
    """Render recent updates (within the last `months` months) as an <ul>."""
    cutoff = months_ago(months)
    recent = sorted(
        (u for u in updates if u[0] >= cutoff), key=lambda u: u[0], reverse=True
    )
    if not recent:
        return ""
    markdown_inline = mistune.create_markdown(plugins=[], escape=False)

    def render_text(text):
        html = markdown_inline(text).strip()
        if html.startswith("<p>") and html.endswith("</p>"):
            html = html[len("<p>"):-len("</p>")]
        return html

    items = "\n".join(
        f'<li><strong>{entry_date.strftime("%b %Y")}</strong> - {render_text(text)}</li>'
        for entry_date, text in recent
    )
    return f"<ul>\n{items}\n</ul>"


def is_generated(path):
    """Return True if `path` is a page this script wrote."""
    return f'<meta name="generator" content="{GENERATOR}">' in path.read_text()


def clean(output_dir):
    """Remove every generated page, including ones no longer in the config."""
    for path in sorted(output_dir.glob("*.html")):
        if is_generated(path):
            path.unlink()
            print(f"\tDeleted {path}")
    for name in GENERATED_FILES:
        path = output_dir / name
        if path.exists():
            path.unlink()
            print(f"\tDeleted {path}")


def generate(config, output_dir):
    """Generate HTML files from markdown content; return the pages written."""
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"), undefined=StrictUndefined
    )
    template = env.get_template("base.html")
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    pages = [*config["pages"].items(), (NOT_FOUND_PAGE, "page not found")]
    for page, label in pages:
        # A fresh renderer per page, so heading ids are unique within a page.
        markdown = mistune.create_markdown(
            renderer=AnchoredRenderer(), plugins=["table"]
        )
        html_content = markdown((ROOT / "content" / f"{page}.md").read_text())
        if UPDATES_MARKER in html_content:
            updates = parse_updates(ROOT / "content" / "updates.txt")
            html_content = html_content.replace(
                UPDATES_MARKER, render_updates(updates)
            )
        descriptions = config["descriptions"]
        rendered = template.render({
            **config,
            "content": html_content,
            "page": f"{page}.html",
            "title": (
                config["title"]
                if page == "index"
                else f"{label.capitalize()} – {config['heading']}"
            ),
            "description": descriptions.get(page, descriptions.get("index", "")),
            "canonical_url": (
                "" if page == NOT_FOUND_PAGE else page_url(config, page)
            ),
            "image_url": f"{config['url']}/{config['photo_path']}",
            "person_json_ld": person_json_ld(config) if page == "index" else "",
            "generator": GENERATOR,
        })
        html_path = output_dir / f"{page}.html"
        print(f"\tRendering {page}.html")
        html_path.write_text(rendered)
        written.append(html_path)
    write_sitemap(config, output_dir)
    return written


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


def serve(output_dir, port):
    """Serve the output directory for local preview."""
    handler = functools.partial(
        SimpleHTTPRequestHandler, directory=str(output_dir)
    )
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {output_dir} at http://localhost:{port}/ (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Static site generator for personal website."
    )
    parser.add_argument(
        "commands",
        nargs="*",
        default=["build"],
        choices=["clean", "build", "serve"],
        help="Commands to run in sequence: 'clean', 'build' and/or 'serve'",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=ROOT / "docs",
        help="Output directory for generated HTML files (default: docs)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port for 'serve' (default: 8000)",
    )
    args = parser.parse_args()
    config = load_config()

    for cmd in args.commands:
        if cmd == "clean":
            print("Cleaning up generated files...")
            clean(args.output)
        elif cmd == "build":
            print("Generating HTML files...")
            written = generate(config, args.output)
            problems = broken_links(args.output, written)
            if problems:
                raise SystemExit(
                    "Broken links found:\n\t" + "\n\t".join(problems)
                )
            print("HTML files generated successfully; all local links resolve.")
        elif cmd == "serve":
            serve(args.output, args.port)
