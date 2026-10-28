"""Interactive commands that add a news item or a publication."""

import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path

import yaml

from .config import ROOT, STATIC_DIR
from .lint import lint_publications
from .publications import PUBLICATIONS_PATH, load_publications
from .updates import parse_updates

UPDATES_PATH = ROOT / "content" / "updates.txt"
URL_RE = re.compile(r"^https?://\S+$")


class Cancelled(Exception):
    """The user pressed Ctrl+C or Ctrl+D at a prompt."""


def ask(question, default="", required=False, check=None):
    """Prompt until the answer is acceptable; return it ('' if skipped)."""
    hint = f" [{default}]" if default else ""
    while True:
        try:
            answer = input(f"{question}{hint}: ").strip()
        except EOFError, KeyboardInterrupt:
            print()
            raise Cancelled from None
        answer = answer or default
        if not answer:
            if required:
                print("  This is required.")
                continue
            return ""
        error = check(answer) if check else None
        if error:
            print(f"  {error}")
            continue
        return answer


def confirm(question, default=True):
    """Ask a yes/no question."""
    answer = ask(f"{question} ({'Y/n' if default else 'y/N'})", check=_yes_no)
    return default if not answer else answer.lower().startswith("y")


def _yes_no(answer):
    return None if answer.lower() in ("y", "yes", "n", "no") else "Answer y or n."


def _check_date(answer):
    try:
        datetime.strptime(answer, "%Y-%m-%d")
    except ValueError:
        return "Use the form YYYY-MM-DD, e.g. 2026-10-28."
    return None


def _check_year(answer):
    if not answer.isdigit() or not 1900 <= int(answer) <= 2100:
        return "Enter a year such as 2026."
    return None


def _insert_line(lines, index, new_line):
    return [*lines[:index], new_line, *lines[index:]]


def add_news():
    """Ask for a news item and insert it into content/updates.txt."""
    try:
        print("Add a news item to content/updates.txt (Ctrl+C to cancel).")
        when = ask("Date", default=date.today().isoformat(), check=_check_date)
        text = ask(
            "Text (Markdown allowed, e.g. *Paper* accepted at ICSE)", required=True
        )
        line = f"{when} | {text}"
        print(f"\n  {line}\n")
        if not confirm("Add this item?"):
            raise Cancelled
    except Cancelled:
        print("Cancelled; nothing changed.")
        return

    lines = UPDATES_PATH.read_text().splitlines() if UPDATES_PATH.exists() else []
    # Keep the log newest first: insert before the first entry not newer.
    index = len(lines)
    for i, existing in enumerate(lines):
        stripped = existing.strip()
        if stripped and not stripped.startswith("#") and stripped[:10] <= when:
            index = i
            break
    original = UPDATES_PATH.read_text() if UPDATES_PATH.exists() else None
    UPDATES_PATH.write_text("\n".join(_insert_line(lines, index, line)) + "\n")
    try:
        parse_updates(UPDATES_PATH)
    except ValueError as e:
        if original is None:
            UPDATES_PATH.unlink()
        else:
            UPDATES_PATH.write_text(original)
        print(f"Not added: {e}")
        return
    print(f"Added to {UPDATES_PATH.relative_to(ROOT)}.")


def _in_static(answer):
    """True if `answer` is a relative path to a file that is already in static/."""
    path = Path(answer)
    return (
        not path.is_absolute()
        and not answer.startswith("~")
        and ((STATIC_DIR / path).is_file())
    )


def ask_file(question, copied):
    """Ask for a PDF/slides link: a URL, a path in static/, or a file to copy.

    Files copied into static/assets/ are appended to `copied`.
    """

    def check(answer):
        if URL_RE.match(answer) or _in_static(answer):
            return None
        if Path(answer).expanduser().is_file():
            return None
        return "Give a URL, a path in static/ (assets/x.pdf), or an existing file."

    answer = ask(question, check=check)
    if not answer or URL_RE.match(answer) or _in_static(answer):
        return answer
    # A file elsewhere on disk: copy it into static/assets/.
    source = Path(answer).expanduser().resolve()
    target = STATIC_DIR / "assets" / source.name
    if target.exists() and not confirm(
        f"  static/assets/{source.name} exists; replace?"
    ):
        raise Cancelled
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    copied.append(target)
    print(f"  Copied to static/assets/{source.name}")
    return f"assets/{source.name}"


def publication_yaml(pub):
    """Format a publication like the entries in publications.yaml."""
    lines = []
    for key, value in pub.items():
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, int):
            text = str(value)
        elif isinstance(value, list):
            text = json.dumps(value, ensure_ascii=False)
        elif key in ("pdf", "slides") and not value.startswith("http"):
            text = value
        else:
            # A JSON string is also a valid double-quoted YAML string.
            text = json.dumps(value, ensure_ascii=False)
        prefix = "- " if not lines else "  "
        lines.append(f"{prefix}{key}: {text}")
    return "\n".join(lines)


def add_paper():
    """Ask for a publication and insert it into content/publications.yaml."""
    copied = []
    known_tags = sorted(
        {tag for pub in load_publications() for tag in pub.get("tags", [])}
    )
    try:
        print("Add a publication to content/publications.yaml (Ctrl+C to cancel).")
        pub = {"title": ask("Title", required=True)}
        authors = ask(
            "Authors, comma-separated (wrap equal contributors in *stars*)",
            required=True,
        )
        pub["authors"] = [a.strip() for a in authors.split(",") if a.strip()]
        pub["venue"] = ask("Venue (full name)", required=True)
        short_venue = ask("Short venue for the home page, e.g. ICSE 2026 (optional)")
        if short_venue:
            pub["short_venue"] = short_venue
        pub["year"] = int(
            ask("Year", default=str(date.today().year), check=_check_year)
        )
        for key, question in (("pdf", "PDF"), ("slides", "Slides")):
            link = ask_file(
                f"{question}: URL, assets/... path, or file to copy (optional)", copied
            )
            if link:
                pub[key] = link
        if known_tags:
            print(f"  Tags in use: {', '.join(known_tags)}")
        tags = ask("Tags, comma-separated (optional)")
        if tags:
            pub["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
        note = ask("Note, e.g. an award (optional)")
        if note:
            pub["note"] = note
        if confirm("Also list it on the home page?", default=False):
            pub["selected"] = True
        entry = publication_yaml(pub)
        print(f"\n{entry}\n")
        if not confirm("Add this publication?"):
            raise Cancelled
    except Cancelled:
        for path in copied:
            path.unlink(missing_ok=True)
        print("Cancelled; nothing changed.")
        return

    original = PUBLICATIONS_PATH.read_text()
    lines = original.splitlines()
    # Newest first: insert before the first entry from the same or an older year.
    nodes = yaml.compose(original)
    index = len(lines)
    for existing, node in zip(load_publications(), nodes.value, strict=True):
        if existing.get("year", 0) <= pub["year"]:
            index = node.start_mark.line
            break
    new_lines = [*lines[:index], *entry.splitlines(), "", *lines[index:]]
    PUBLICATIONS_PATH.write_text("\n".join(new_lines).rstrip("\n") + "\n")
    errors = [m for level, m in lint_publications() if level == "error"]
    if errors:
        PUBLICATIONS_PATH.write_text(original)
        for path in copied:
            path.unlink(missing_ok=True)
        print("Not added; the entry has problems:\n  " + "\n  ".join(errors))
        return
    print(f"Added to {PUBLICATIONS_PATH.relative_to(ROOT)}.")
