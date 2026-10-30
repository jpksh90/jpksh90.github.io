# jpksh90.github.io

[![Deploy Clean Build](https://github.com/jpksh90/jpksh90.github.io/actions/workflows/clean-build-deploy.yml/badge.svg)](https://github.com/jpksh90/jpksh90.github.io/actions/workflows/clean-build-deploy.yml)

Source for <https://jpksh90.github.io>.

## Editing the site

| To change | Edit |
| --- | --- |
| Page text | `content/<page>.md` |
| Publications | `content/publications.yaml` (`selected: true` also lists a paper on the home page) |
| News | `content/updates.txt`, one `YYYY-MM-DD \| text` line per item |
| Name, links, menu, page descriptions | `config.yaml` |
| PDFs, images | `static/` (e.g. `static/assets/paper.pdf`, linked as `assets/paper.pdf`) |
| Page layout, profile-link icons, stylesheet | see [Theme](#theme) |

The home page's "E-mail:" line comes from `email` and `official_email` in
`config.yaml`. JPEG and PNG photos under `static/images/` are served as WebP in
several sizes automatically. Never edit `docs/`; it is generated.

## Theme

The default theme ships inside sitegen, in `sitegen/theme/`:

| File | Replace it with |
| --- | --- |
| `templates/base.html` (page layout) | `templates/base.html` |
| `templates/icons.html` (profile-link icons) | `templates/icons.html` |
| `static/stylesheets/styles.css` | `static/stylesheets/styles.css` |

To change one, copy it from `sitegen/theme/` to the same path in this
repository and edit the copy; it replaces the theme's file, and the others
still come from the theme. A site therefore needs only `config.yaml` and
`content/`; `static/` and `templates/` are optional.

## Building

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run sitegen add-news      # add a dated news item (asks questions)
uv run sitegen add-paper     # add a publication; can copy its PDF into static/assets/
uv run sitegen build serve   # build into docs/ and preview at http://localhost:8000
uv run sitegen lint          # check config.yaml and publications.yaml only
uv run sitegen publish       # lint, build, then commit and push your changes
uv run sitegen publish -y -m "Fix typo"   # the same, without questions
```

sitegen works on the nearest folder above the current one that holds a
`config.yaml`, so it runs from any subfolder of the site. To build another
site with this copy of sitegen, run it from that site's folder:
`uv run --project /path/to/this/repo sitegen build`.

## Starting a new site

In an empty folder (ideally a fresh git repository), run:

```sh
uv tool install git+https://github.com/jpksh90/jpksh90.github.io
sitegen init        # asks for your name, email and site URL; -y takes the suggestions
sitegen build serve
```

This writes `config.yaml`, `content/index.md`, `content/404.md`, a
placeholder photo, a `.gitignore` and a GitHub Actions workflow that deploys
to a `deploy` branch. In the repository's Settings > Pages, choose "Deploy
from a branch", branch `deploy`, folder `/docs`. `sitegen publish` pushes to
the branch named by `branch` in `config.yaml` (default `main`).

The build stops with a message, leaving `docs/` untouched, if the config has
errors or any page links to a missing file or `#section`.

## Publishing

Run `uv run sitegen publish`, or commit and push to `main` yourself. GitHub Actions checks the code with ruff, builds the site and
publishes it to the `deploy` branch, which GitHub Pages serves. It also
rebuilds every Monday so old news drops off; if nothing changed, it skips the
deploy.
