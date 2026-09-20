import argparse
import os
from datetime import date, datetime

import mistune
import yaml
from jinja2 import Environment, FileSystemLoader

UPDATES_MARKER = "<!-- UPDATES -->"
UPDATES_WINDOW_MONTHS = 3


# Load config file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    title = config.get('title', 'My Personal Website')
    email = config.get('email', '')
    heading = config.get('heading', '')
    github = config.get('github', '')
    linkedin = config.get('linkedin', '')
    twitter = config.get('twitter', '')
    google_scholar = config.get('google_scholar', '')
    pages = config.get('pages', {})
    photo_credit = config.get('photo_credit', '')
    photo_path = config.get('photo_path', 'images/Photo-Indian-Passport.jpg')


def normalize_public_path(path):
    """Return an asset path relative to the published docs root."""
    normalized = os.path.normpath(path).replace("\\", "/")
    if normalized.startswith("../docs/"):
        return normalized[len("../docs/"):]
    if normalized.startswith("docs/"):
        return normalized[len("docs/"):]
    return normalized


env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('base.html')


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


def clean_pages(pages, output_dir):
    """Remove generated HTML files for the given pages."""
    for page in pages:
        html_file = os.path.join(output_dir, f"{page}.html")
        if os.path.exists(html_file):
            os.remove(html_file)
            print(f"\tDeleted {html_file}")


def generate(output_dir):
    """Generate HTML files from markdown content."""
    for page,_ in pages.items():
        with open(f"content/{page}.md") as f:
            md_content = f.read()
        markdown = mistune.create_markdown(plugins=['table'], escape=False)
        html_content = markdown(md_content)
        if UPDATES_MARKER in html_content:
            updates = parse_updates("content/updates.txt")
            html_content = html_content.replace(
                UPDATES_MARKER, render_updates(updates)
            )
        rendered = template.render(
            content=html_content,
            page=f"{page}.html",
            title=title,
            email=email,
            heading=heading,
            github=github,
            linkedin=linkedin,
            twitter=twitter,
            google_scholar=google_scholar,
            photo_credit=photo_credit,
            photo_path=normalize_public_path(photo_path),
            pages=pages,
        )
        html_path = os.path.join(output_dir, f"{page}.html")
        with open(html_path, "w") as f:
            print(f"\tRendering {page}.html")
            f.write(rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Static site generator for personal website."
    )
    parser.add_argument(
        "commands",
        nargs="*",
        default=["build"],
        choices=["clean", "build"],
        help="Commands to run: 'build', 'clean', or both in sequence"
    )
    parser.add_argument(
        "-o", "--output",
        default="docs",
        help="Output directory for generated HTML files (default: docs)"
    )
    args = parser.parse_args()

    for cmd in args.commands:
        if cmd == "clean":
            print("Cleaning up old HTML files...")
            clean_pages(pages, output_dir=args.output)
        elif cmd == "build":
            print("Generating HTML files...")
            generate(output_dir=args.output)
            print("HTML files generated successfully.")
