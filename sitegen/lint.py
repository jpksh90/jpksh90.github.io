"""Checks for config.yaml and content/publications.yaml."""

import re
import sys

import yaml

from .config import (
    CONFIG_DEFAULTS,
    NOT_FOUND_PAGE,
    ROOT,
    STATIC_DIR,
    normalize_public_path,
)
from .publications import PUBLICATION_FIELDS, PUBLICATIONS_PATH
from .render import template_env
from .updates import parse_updates

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
    for key in ("email", "official_email"):
        value = raw.get(key)
        if key in raw and not isinstance(value, str):
            report("error", (key,), f"'{key}' must be text")
        elif value and not EMAIL_RE.match(value):
            report("error", (key,), f"{key} '{value}' is not an address")
    for key in ("job_title", "affiliation", "photo_credit"):
        if key in raw and not isinstance(raw[key], str):
            report("error", (key,), f"'{key}' must be text")

    pages = raw.get("pages")
    if not isinstance(pages, dict) or not pages:
        report("error", ("pages",), "'pages' must list at least one page")
        pages = {}
    for page, label in pages.items():
        if not isinstance(page, str):
            report(
                "error",
                ("pages",),
                f'page name {page} is a number; write it as "{page}"',
            )
            continue
        if page == NOT_FOUND_PAGE:
            report(
                "error",
                ("pages", page),
                f"'{page}' is built automatically; remove it from pages",
            )
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
            report(
                "error",
                ("descriptions", str(page)),
                f'description key {page} is a number; write it as "{page}"',
            )
            continue
        if page not in pages and page != NOT_FOUND_PAGE:
            report(
                "warning",
                ("descriptions", page),
                f"description for '{page}', which is not in pages",
            )
        if not isinstance(description, str) or not description.strip():
            report(
                "error",
                ("descriptions", page),
                f"description for '{page}' must be text",
            )
        elif len(description) > DESCRIPTION_MAX:
            report(
                "warning",
                ("descriptions", page),
                f"description for '{page}' is {len(description)} characters; "
                f"search results cut it off after about {DESCRIPTION_MAX}",
            )
    for page in [*pages, NOT_FOUND_PAGE]:
        if isinstance(page, str) and page not in descriptions:
            report(
                "warning",
                ("descriptions",),
                f"no description for '{page}'; the home page's will be used",
            )

    links = raw.get("links", {})
    if not isinstance(links, dict):
        report("error", ("links",), "'links' must map names to URLs")
        links = {}
    icons = template_env().get_template("icons.html").module.icons
    for name, href in links.items():
        if name not in icons:
            report(
                "error",
                ("links", str(name)),
                f"no icon for link '{name}' in templates/icons.html "
                f"(available: {', '.join(icons)})",
            )
        if not isinstance(href, str) or not URL_RE.match(href):
            report(
                "error",
                ("links", str(name)),
                f"link '{name}' must be an http(s) URL, got {href!r}",
            )

    photo_path = raw.get("photo_path", CONFIG_DEFAULTS["photo_path"])
    if not isinstance(photo_path, str):
        report("error", ("photo_path",), "'photo_path' must be text")
    elif not (STATIC_DIR / normalize_public_path(photo_path)).is_file():
        report("error", ("photo_path",), f"photo '{photo_path}' is not in static/")

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

    for pub, node in zip(pubs, nodes.value, strict=True):
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
            report(
                "error", line, "every author must be text; quote names starting with *"
            )
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
