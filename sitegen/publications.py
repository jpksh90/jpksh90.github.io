"""Publication lists rendered from content/publications.yaml."""

import yaml

from .config import ROOT

PUBLICATIONS_MARKER = "<!-- PUBLICATIONS -->"
SELECTED_PUBLICATIONS_MARKER = "<!-- SELECTED_PUBLICATIONS -->"
PUBLICATIONS_PATH = ROOT / "content" / "publications.yaml"
PUBLICATION_FIELDS = {
    "title",
    "authors",
    "venue",
    "short_venue",
    "year",
    "pdf",
    "slides",
    "tags",
    "note",
    "selected",
}
PDF_ICON = '<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>'
SLIDES_ICON = '<i class="fa-solid fa-file-powerpoint" aria-hidden="true"></i>'


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
        publication_markdown(pub, short=True) for pub in pubs if pub.get("selected")
    )
