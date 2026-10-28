"""Site configuration: config.yaml loading and URL helpers."""

import os
from pathlib import Path

import yaml

# Repository root: content/, templates/, static/ and config.yaml live here.
ROOT = Path(__file__).resolve().parent.parent
# Files copied unchanged to the site root: PDFs, images, stylesheets, ...
STATIC_DIR = ROOT / "static"
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
}


def normalize_public_path(path):
    """Return an asset path relative to the site root ('images/x.jpg')."""
    normalized = os.path.normpath(path).replace("\\", "/")
    for prefix in ("../static/", "static/", "../docs/", "docs/"):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
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
