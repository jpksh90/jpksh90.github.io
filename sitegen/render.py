"""Rendering pages, the sitemap and robots.txt, and cleaning output."""

import json
import re
from html import unescape

import mistune
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config import NOT_FOUND_PAGE, ROOT, page_url
from .publications import (
    PUBLICATIONS_MARKER,
    SELECTED_PUBLICATIONS_MARKER,
    load_publications,
    render_publications,
    render_selected_publications,
)
from .updates import UPDATES_MARKER, parse_updates, render_updates

# Written into every generated page so `clean` only deletes our own output.
GENERATOR = "site-utils.py"
GENERATED_FILES = ("sitemap.xml", "robots.txt")


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
        f"  <url><loc>{page_url(config, page)}</loc></url>" for page in config["pages"]
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
            html_content = html_content.replace(UPDATES_MARKER, render_updates(updates))
        descriptions = config["descriptions"]
        rendered = template.render(
            {
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
            }
        )
        html_path = output_dir / f"{page}.html"
        print(f"\tRendering {page}.html")
        html_path.write_text(rendered)
        written.append(html_path)
    write_sitemap(config, output_dir)
    return written
