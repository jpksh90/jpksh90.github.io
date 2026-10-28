import argparse
import functools
import json
import os
import re
import sys
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
PUBLICATIONS_MARKER = "<!-- PUBLICATIONS -->"
SELECTED_PUBLICATIONS_MARKER = "<!-- SELECTED_PUBLICATIONS -->"
PUBLICATIONS_PATH = ROOT / "content" / "publications.yaml"
PUBLICATION_FIELDS = {
    "title", "authors", "venue", "short_venue", "year",
    "pdf", "slides", "tags", "note", "selected",
}
PDF_ICON = '<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>'
SLIDES_ICON = '<i class="fa-solid fa-file-powerpoint" aria-hidden="true"></i>'
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


def load_publications(path=PUBLICATIONS_PATH):
    """Return the list of publications, or [] if there is no data file."""
    if not path.exists():
        return []
    with open(path) as f:
        return yaml.safe_load(f) or []


def publication_markdown(pub, short=False):
    """Render one publication as a Markdown list item.

    The short form (home page) drops tags and notes and uses short_venue.
    """
    head = f"- **{pub['title']}**"
    links = []
    if pub.get("pdf"):
        links.append(f"[{PDF_ICON}]({pub['pdf']})")
    if pub.get("slides"):
        links.append(f"[{SLIDES_ICON}]({pub['slides']})")
    if links:
        head += " " + " ".join(links)
    lines = [head]
    if not short and pub.get("tags"):
        lines.append(" ".join(f"`{tag}`" for tag in pub["tags"]))
    lines.append(", ".join(pub["authors"]))
    venue = pub.get("short_venue", pub["venue"]) if short else pub["venue"]
    lines.append(f"*{venue}*")
    if not short and pub.get("note"):
        lines.append(pub["note"])
    return "<br>\n  ".join(lines)


def render_publications(pubs):
    """Render all publications as Markdown, grouped under year headings."""
    by_year = {}
    for pub in pubs:
        by_year.setdefault(pub["year"], []).append(pub)
    return "\n\n".join(
        f"#### {year}\n\n"
        + "\n\n".join(publication_markdown(pub) for pub in by_year[year])
        for year in sorted(by_year, reverse=True)
    )


def render_selected_publications(pubs):
    """Render the publications marked `selected` in their short form."""
    return "\n\n".join(
        publication_markdown(pub, short=True)
        for pub in pubs
        if pub.get("selected")
    )


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


def template_env():
    """Return the Jinja environment; undefined variables are errors."""
    return Environment(
        loader=FileSystemLoader(ROOT / "templates"), undefined=StrictUndefined
    )


URL_RE = re.compile(r"^https?://[^\s/]+\S*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Search engines cut descriptions off at roughly this many characters.
DESCRIPTION_MAX = 160


def yaml_key_lines(text):
    """Map key paths such as ('links', 'github') to their line in the YAML."""
    lines = {}

    def walk(node, path):
        if isinstance(node, yaml.MappingNode):
            for key, value in node.value:
                key_path = (*path, key.value)
                lines[key_path] = key.start_mark.line + 1
                walk(value, key_path)

    walk(yaml.compose(text), ())
    return lines


def lint_config(path=ROOT / "config.yaml"):
    """Check config.yaml and the files it refers to.

    Returns a list of (level, message) pairs, where level is "error" (the
    build would fail or produce a broken page) or "warning" (likely a mistake).
    """
    text = path.read_text()
    try:
        raw = yaml.safe_load(text)
        lines = yaml_key_lines(text)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        line = mark.line + 1 if mark else 1
        problem = getattr(e, "problem", None) or e
        return [("error", f"{path.name}:{line}: error: invalid YAML: {problem}")]

    issues = []

    def report(level, keys, message):
        # Point at the most specific key that exists in the file.
        line = next(
            (lines[keys[:i]] for i in range(len(keys), 0, -1) if keys[:i] in lines),
            1,
        )
        issues.append((level, f"{path.name}:{line}: {level}: {message}"))

    if not isinstance(raw, dict):
        report("error", (), "expected a list of 'key: value' settings")
        return issues

    for key in raw:
        if key not in CONFIG_DEFAULTS:
            report("warning", (key,), f"unknown setting '{key}' (typo?)")

    for key in ("title", "heading", "url", "email"):
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            report("error", (key,), f"'{key}' must be set to some text")
    if isinstance(raw.get("url"), str) and not URL_RE.match(raw["url"]):
        report("error", ("url",), f"url '{raw['url']}' is not an http(s) URL")
    if isinstance(raw.get("email"), str) and not EMAIL_RE.match(raw["email"]):
        report("error", ("email",), f"email '{raw['email']}' is not an address")
    for key in ("job_title", "affiliation", "photo_credit"):
        if key in raw and not isinstance(raw[key], str):
            report("error", (key,), f"'{key}' must be text")

    pages = raw.get("pages")
    if not isinstance(pages, dict) or not pages:
        report("error", ("pages",), "'pages' must list at least one page")
        pages = {}
    for page, label in pages.items():
        if not isinstance(page, str):
            report("error", ("pages",),
                   f"page name {page} is a number; write it as \"{page}\"")
            continue
        if page == NOT_FOUND_PAGE:
            report("error", ("pages", page),
                   f"'{page}' is built automatically; remove it from pages")
        elif not (ROOT / "content" / f"{page}.md").is_file():
            report("error", ("pages", page), f"no content/{page}.md for page '{page}'")
        if not isinstance(label, str) or not label.strip():
            report("error", ("pages", page), f"page '{page}' needs a menu label")
    if pages and "index" not in pages:
        report("error", ("pages",), "'pages' must include 'index' (the home page)")
    if not (ROOT / "content" / f"{NOT_FOUND_PAGE}.md").is_file():
        report("error", ("pages",), f"no content/{NOT_FOUND_PAGE}.md for the 404 page")

    descriptions = raw.get("descriptions", {})
    if not isinstance(descriptions, dict):
        report("error", ("descriptions",), "'descriptions' must map pages to text")
        descriptions = {}
    for page, description in descriptions.items():
        if not isinstance(page, str):
            report("error", ("descriptions", str(page)),
                   f"description key {page} is a number; write it as \"{page}\"")
            continue
        if page not in pages and page != NOT_FOUND_PAGE:
            report("warning", ("descriptions", page),
                   f"description for '{page}', which is not in pages")
        if not isinstance(description, str) or not description.strip():
            report("error", ("descriptions", page),
                   f"description for '{page}' must be text")
        elif len(description) > DESCRIPTION_MAX:
            report("warning", ("descriptions", page),
                   f"description for '{page}' is {len(description)} characters; "
                   f"search results cut it off after about {DESCRIPTION_MAX}")
    for page in [*pages, NOT_FOUND_PAGE]:
        if isinstance(page, str) and page not in descriptions:
            report("warning", ("descriptions",),
                   f"no description for '{page}'; the home page's will be used")

    links = raw.get("links", {})
    if not isinstance(links, dict):
        report("error", ("links",), "'links' must map names to URLs")
        links = {}
    icons = template_env().get_template("icons.html").module.icons
    for name, href in links.items():
        if name not in icons:
            report("error", ("links", str(name)),
                   f"no icon for link '{name}' in templates/icons.html "
                   f"(available: {', '.join(icons)})")
        if not isinstance(href, str) or not URL_RE.match(href):
            report("error", ("links", str(name)),
                   f"link '{name}' must be an http(s) URL, got {href!r}")

    photo_path = raw.get("photo_path", CONFIG_DEFAULTS["photo_path"])
    if not isinstance(photo_path, str):
        report("error", ("photo_path",), "'photo_path' must be text")
    elif not (ROOT / "docs" / normalize_public_path(photo_path)).is_file():
        report("error", ("photo_path",), f"photo '{photo_path}' does not exist")

    updates_path = ROOT / "content" / "updates.txt"
    try:
        parse_updates(updates_path)
    except ValueError as e:
        # parse_updates reports "<path>:<line>: <problem>".
        location, problem = str(e).split(": ", 1)
        location = location.replace(f"{ROOT}/", "")
        issues.append(("error", f"{location}: error: {problem}"))

    return issues


def lint_publications(path=PUBLICATIONS_PATH):
    """Check the publications data file; same return format as lint_config."""
    if not path.exists():
        return []
    name = path.relative_to(ROOT)
    text = path.read_text()
    try:
        pubs = yaml.safe_load(text)
        nodes = yaml.compose(text)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        line = mark.line + 1 if mark else 1
        problem = getattr(e, "problem", None) or e
        return [("error", f"{name}:{line}: error: invalid YAML: {problem}")]
    if pubs is None:
        return []

    issues = []

    def report(level, line, message):
        issues.append((level, f"{name}:{line}: {level}: {message}"))

    if not isinstance(pubs, list):
        report("error", 1, "expected a list of publications ('- title: ...')")
        return issues

    def is_text(value):
        return isinstance(value, str) and value.strip()

    for pub, node in zip(pubs, nodes.value):
        line = node.start_mark.line + 1
        if not isinstance(pub, dict):
            report("error", line, "each publication must be a set of fields")
            continue
        for key in pub:
            if key not in PUBLICATION_FIELDS:
                report("warning", line, f"unknown field '{key}' (typo?)")
        for key in ("title", "venue"):
            if not is_text(pub.get(key)):
                report("error", line, f"publication needs a '{key}'")
        authors = pub.get("authors")
        if not isinstance(authors, list) or not authors:
            report("error", line, "'authors' must be a list of names")
        elif not all(is_text(author) for author in authors):
            report("error", line,
                   "every author must be text; quote names starting with *")
        if not isinstance(pub.get("year"), int) or isinstance(pub.get("year"), bool):
            report("error", line, "'year' must be a number such as 2026")
        for key in ("short_venue", "pdf", "slides", "note"):
            if key in pub and not is_text(pub[key]):
                report("error", line, f"'{key}' must be text")
        tags = pub.get("tags", [])
        if not isinstance(tags, list) or not all(is_text(tag) for tag in tags):
            report("error", line, "'tags' must be a list such as [cross-language]")
        if not isinstance(pub.get("selected", False), bool):
            report("error", line, "'selected' must be true or false")
    return issues


def run_lint():
    """Print config problems; exit if any are errors."""
    issues = lint_config() + lint_publications()
    for _, message in issues:
        print(message, file=sys.stderr)
    errors = sum(level == "error" for level, _ in issues)
    if errors:
        raise SystemExit(f"{errors} config error(s) found; nothing was built.")
    return issues


def generate(config, output_dir):
    """Generate HTML files from markdown content; return the pages written."""
    template = template_env().get_template("base.html")
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    pages = [*config["pages"].items(), (NOT_FOUND_PAGE, "page not found")]
    publications = load_publications()
    for page, label in pages:
        # A fresh renderer per page, so heading ids are unique within a page.
        markdown = mistune.create_markdown(
            renderer=AnchoredRenderer(), plugins=["table"]
        )
        md_content = (ROOT / "content" / f"{page}.md").read_text()
        md_content = md_content.replace(
            PUBLICATIONS_MARKER, render_publications(publications)
        ).replace(
            SELECTED_PUBLICATIONS_MARKER,
            render_selected_publications(publications),
        )
        html_content = markdown(md_content)
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
        choices=["lint", "clean", "build", "serve"],
        help="Commands to run in sequence: 'lint', 'clean', 'build', 'serve'",
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

    for cmd in args.commands:
        if cmd == "lint":
            issues = run_lint()
            print(f"Config OK ({len(issues)} warning(s)).")
        elif cmd == "clean":
            print("Cleaning up generated files...")
            clean(args.output)
        elif cmd == "build":
            run_lint()
            print("Generating HTML files...")
            written = generate(load_config(), args.output)
            problems = broken_links(args.output, written)
            if problems:
                raise SystemExit(
                    "Broken links found:\n\t" + "\n\t".join(problems)
                )
            print("HTML files generated successfully; all local links resolve.")
        elif cmd == "serve":
            serve(args.output, args.port)
