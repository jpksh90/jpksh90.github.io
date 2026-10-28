"""The news log in content/updates.txt."""

import os
from datetime import date, datetime

import mistune

UPDATES_MARKER = "<!-- UPDATES -->"
UPDATES_WINDOW_MONTHS = 3


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
            html = html[len("<p>") : -len("</p>")]
        return html

    items = "\n".join(
        f"<li><strong>{when:%b %Y}</strong> - {render_text(text)}</li>"
        for when, text in recent
    )
    return f"<ul>\n{items}\n</ul>"
