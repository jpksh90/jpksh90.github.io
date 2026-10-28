# jpksh90.github.io

[![Deploy Clean Build](https://github.com/jpksh90/jpksh90.github.io/actions/workflows/clean-build-deploy.yml/badge.svg)](https://github.com/jpksh90/jpksh90.github.io/actions/workflows/clean-build-deploy.yml)

Source for <https://jpksh90.github.io>, built with a small static site
generator (the `sitegen/` package, run through `site-utils.py`) from Markdown
and a Jinja template.

## Layout

| Path | What it holds |
| --- | --- |
| `content/*.md` | One Markdown file per page (`index`, `research`, `teaching`, `service`, `team`, `404`). Raw HTML is allowed. |
| `content/publications.yaml` | Every publication, once. Rendered in full on the research page (`<!-- PUBLICATIONS -->`) and, for entries with `selected: true`, on the home page (`<!-- SELECTED_PUBLICATIONS -->`). |
| `content/updates.txt` | News log, one `YYYY-MM-DD \| text` entry per line. Only the last 3 months are shown, wherever `<!-- UPDATES -->` appears in a page. |
| `config.yaml` | Name, email, site URL, profile links, navigation, and per-page meta descriptions. |
| `templates/base.html` | Page layout shared by every page. |
| `templates/icons.html` | Sidebar icons, one per entry in `links` in `config.yaml`. |
| `static/` | Files copied unchanged to the site root: PDFs in `assets/`, `images/`, `stylesheets/`, `javascripts/`, `favicon.ico`, the Google verification file. |
| `docs/` | The built site (`static/` plus the generated pages). Not committed. |

## Editing

- **Page text**: edit `content/<page>.md`.
- **Publications**: add an entry at the top of `content/publications.yaml`
  (the field list is at the top of the file). Set `selected: true` to also
  show it on the home page, with `short_venue` as its venue there.
- **News**: add a line to the top of `content/updates.txt`.
- **Profile links**: add, remove or reorder entries under `links` in
  `config.yaml`. A new link name also needs an icon in `templates/icons.html`.
- **New page**: add `content/<name>.md`, then add it to `pages` and
  `descriptions` in `config.yaml`.
- **Papers and slides**: put PDFs in `static/assets/` and link them as
  `assets/<file>.pdf`.

Do not edit anything in `docs/`; it is rebuilt from scratch on every build.

## Building and previewing

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run site-utils.py build serve
```

This rebuilds the site into `docs/` and serves it at
<http://localhost:8000/>. The build fails if any page links to a local file
that is missing or empty, or to a `#section` that does not exist.

Every Markdown heading gets an id from its text, so sections can be linked
directly, e.g. `research.html#talks` for `### 🎤 Talks`. Renaming a heading
changes its id; the build then reports any links that still use the old one.

Commands can be combined in any order:

- `lint` checks `config.yaml` and the files it refers to, reporting each
  problem with its line number: missing settings, malformed URLs or email,
  pages without a content file or description, profile links without an
  icon, a missing photo, unquoted `404` keys, unknown (misspelled) settings,
  over-long descriptions, malformed lines in `content/updates.txt`, and
  missing or mistyped fields in `content/publications.yaml`.
  `build` runs it first and stops on errors; warnings do not stop the build.
- `clean` deletes the built site in `docs/`. It only deletes a folder that
  `build` created, so a wrong `-o` cannot remove anything else.
- `build` copies `static/`, renders the pages, `sitemap.xml` and `robots.txt`,
  then checks links. It works in a hidden staging folder and replaces `docs/`
  only if everything succeeds, so a failed build leaves the previous `docs/`
  untouched. Each build starts from scratch, so stale files never linger and
  `clean` is not needed first.
- `serve` starts a local preview server (`-p` to change the port).

Use `-o <dir>` to build somewhere other than `docs/`.

## Generator code

`site-utils.py` only starts the command-line interface; the generator is the
`sitegen/` package:

| Module | Responsibility |
| --- | --- |
| `cli.py` | Command-line interface (`lint`, `clean`, `build`, `serve`). |
| `config.py` | Loading `config.yaml` with defaults; page URLs. |
| `render.py` | Rendering pages from Markdown and the template; sitemap, robots.txt; `clean`. |
| `publications.py` | Publication lists from `content/publications.yaml`. |
| `updates.py` | The news list from `content/updates.txt`. |
| `lint.py` | Checks for `config.yaml` and `content/publications.yaml`. |
| `links.py` | Checking local links and `#fragments` in the built pages. |
| `serve.py` | Local preview server. |

Code is linted and formatted with [ruff](https://docs.astral.sh/ruff/)
(settings in `pyproject.toml`). CI fails if either check fails; run them
locally with:

```sh
uvx ruff@0.15.10 check --fix .
uvx ruff@0.15.10 format .
```

## Deployment

Pushing to `main` runs `.github/workflows/clean-build-deploy.yml`, which
runs the ruff checks, builds the site and force-pushes the result to the `deploy` branch. GitHub
Pages serves the `docs/` folder of that branch. The workflow also runs every
Monday so the news list drops entries older than 3 months.

## License

The original theme is based on
[Minimal](https://github.com/orderedlist/minimal), licensed under
[CC BY-SA 3.0](http://creativecommons.org/licenses/by-sa/3.0/).
