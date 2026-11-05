"""Site configuration: config.yaml loading and URL helpers."""

import os
from pathlib import Path

import yaml


def find_site_root(start=None):
    """Return the nearest folder holding config.yaml, from `start` upwards.

    Like git, sitegen works from any subfolder of the site. Falls back to
    `start` itself (the current folder) so `sitegen --help` works anywhere.
    """
    start = Path(start or Path.cwd()).resolve()
    for folder in (start, *start.parents):
        if (folder / "config.yaml").is_file():
            return folder
    return start


# Site root: content/, templates/, static/ and config.yaml live here.
ROOT = find_site_root()
# Files copied unchanged to the site root: PDFs, images, stylesheets, ...
STATIC_DIR = ROOT / "static"
# Optional; a template here replaces the theme's template of the same name.
TEMPLATES_DIR = ROOT / "templates"
# Themes shipped with sitegen, one folder each with templates/ and static/.
# Other themes build on the default one: a file is looked up in the site,
# then the chosen theme, then the default theme.
THEMES_DIR = Path(__file__).resolve().parent / "themes"
DEFAULT_THEME = "default"
# Rendered like the other pages, but kept out of the nav and sitemap.
NOT_FOUND_PAGE = "404"

CONFIG_DEFAULTS = {
    "title": "My Personal Website",
    "email": "",
    "official_email": "",
    "heading": "",
    "url": "",
    "job_title": "",
    "affiliation": "",
    "links": {},
    "pages": {},
    "descriptions": {},
    "photo_credit": "",
    "photo_path": "images/headshot.jpg",
    # The git branch that `publish` commits to and CI deploys from
    "branch": "main",
    # A folder in sitegen/themes/
    "theme": DEFAULT_THEME,
}


def normalize_public_path(path):
    """Return an asset path relative to the site root ('images/x.jpg')."""
    normalized = os.path.normpath(path).replace("\\", "/")
    for prefix in ("../static/", "static/", "../docs/", "docs/"):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def available_themes():
    """Names of the themes shipped with sitegen."""
    return sorted(path.name for path in THEMES_DIR.iterdir() if path.is_dir())


def theme_dirs(theme):
    """The theme folders to look in, most specific first."""
    dirs = [THEMES_DIR / theme]
    if theme != DEFAULT_THEME:
        dirs.append(THEMES_DIR / DEFAULT_THEME)
    return dirs


def static_file(path, theme):
    """Return the file served at `path`: the site's own, else the theme's."""
    for static_dir in (STATIC_DIR, *(d / "static" for d in theme_dirs(theme))):
        if (static_dir / path).is_file():
            return static_dir / path
    return STATIC_DIR / path


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
