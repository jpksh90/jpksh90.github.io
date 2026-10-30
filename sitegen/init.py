"""`sitegen init`: write a starter site into the current folder."""

import json
from pathlib import Path
from string import Template

from .add import Cancelled, ask
from .lint import EMAIL_RE, URL_RE
from .publish import git, github_repo

STARTER_DIR = Path(__file__).resolve().parent / "starter"
# Where the starter's workflow installs sitegen from.
SITEGEN_SOURCE = "git+https://github.com/jpksh90/jpksh90.github.io"
# Packaging tools skip dotfiles, so the starter stores them as dot-<name>.
DOT_PREFIX = "dot-"
# Starter files whose $placeholders are filled in; the rest are copied as is.
TEMPLATED = {"config.yaml", "content/index.md", "dot-github/workflows/deploy.yml"}


def starter_files():
    """Map each starter file to its path in the new site."""
    files = {}
    for source in sorted(STARTER_DIR.rglob("*")):
        if source.is_file() and source.name != ".DS_Store":
            relative = source.relative_to(STARTER_DIR)
            parts = [
                "." + part.removeprefix(DOT_PREFIX)
                if part.startswith(DOT_PREFIX)
                else part
                for part in relative.parts
            ]
            files[source] = Path(*parts)
    return files


def default_url(folder):
    """Guess the GitHub Pages URL from the `origin` remote, if there is one."""
    repo = github_repo(cwd=folder)
    if not repo:
        return "https://example.org"
    owner, name = repo
    if name.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner.lower()}.github.io"
    return f"https://{owner.lower()}.github.io/{name}"


def _check(pattern, what):
    return lambda answer: None if pattern.match(answer) else f"Enter {what}."


def init(yes=False):
    """Ask for a name, email and URL, then write the starter site.

    With `yes`, the defaults (from git where possible) are used without asking.
    Nothing is written if any of the files already exists.
    """
    folder = Path.cwd()
    files = starter_files()
    existing = [str(target) for target in files.values() if (folder / target).exists()]
    if existing:
        raise SystemExit(
            f"Not overwriting existing files in {folder}: {', '.join(existing)}"
        )

    defaults = {
        "name": git("config", "user.name", check=False, cwd=folder).strip()
        or "Your Name",
        "email": git("config", "user.email", check=False, cwd=folder).strip()
        or "you@example.org",
        "url": default_url(folder),
    }
    if yes:
        answers = defaults
    else:
        print(f"Creating a new site in {folder}. Press Enter to keep a suggestion.")
        try:
            answers = {
                "name": ask("Your name", defaults["name"], required=True),
                "email": ask(
                    "Email address",
                    defaults["email"],
                    required=True,
                    check=_check(EMAIL_RE, "an address such as you@example.org"),
                ),
                "url": ask(
                    "Site URL",
                    defaults["url"],
                    required=True,
                    check=_check(URL_RE, "an http(s) URL"),
                ),
            }
        except Cancelled:
            print("Cancelled; nothing was written.")
            return

    name = answers["name"]
    values = {
        # JSON strings are valid YAML, so names with quotes or colons are safe.
        "name": json.dumps(name, ensure_ascii=False),
        "email": json.dumps(answers["email"]),
        "url": json.dumps(answers["url"].rstrip("/")),
        "description": json.dumps(
            f"The personal website of {name}.", ensure_ascii=False
        ),
        "plain_name": name,
        "branch": git("branch", "--show-current", check=False, cwd=folder).strip()
        or "main",
        "sitegen_source": SITEGEN_SOURCE,
    }
    for source, target in files.items():
        path = folder / target
        path.parent.mkdir(parents=True, exist_ok=True)
        if source.relative_to(STARTER_DIR).as_posix() in TEMPLATED:
            path.write_text(Template(source.read_text()).safe_substitute(values))
        else:
            path.write_bytes(source.read_bytes())
        print(f"\tWrote {target}")

    print(
        "\nNext steps:\n"
        "  1. Install sitegen:  uv tool install " + SITEGEN_SOURCE + "\n"
        "  2. Preview:          sitegen build serve\n"
        "  3. Edit config.yaml and content/, and replace static/images/photo.svg\n"
        "  4. Push to GitHub; in Settings > Pages choose 'Deploy from a branch',\n"
        "     branch 'deploy', folder /docs. After that, `sitegen publish` deploys."
    )
