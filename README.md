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
| PDFs, images, stylesheets | `static/` (e.g. `static/assets/paper.pdf`, linked as `assets/paper.pdf`) |
| Page layout | `templates/base.html` |

Never edit `docs/`; it is generated.

## Building

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run site-utils.py build serve   # build into docs/ and preview at http://localhost:8000
uv run site-utils.py lint          # check config.yaml and publications.yaml only
```

The build stops with a message, leaving `docs/` untouched, if the config has
errors or any page links to a missing file or `#section`.

## Publishing

Push to `main`. GitHub Actions checks the code with ruff, builds the site and
publishes it to the `deploy` branch, which GitHub Pages serves. It also
rebuilds every Monday so old news drops off; if nothing changed, it skips the
deploy.
