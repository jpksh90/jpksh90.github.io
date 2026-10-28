"""`sitegen publish`: check, build, commit and push the site in one step."""

import subprocess

from .add import Cancelled, ask, confirm
from .build import build
from .config import ROOT, load_config
from .lint import run_lint

BRANCH = "main"
ACTIONS_URL = "https://github.com/jpksh90/jpksh90.github.io/actions"

# Suggested commit message parts, by the first changed path that matches.
MESSAGE_HINTS = (
    ("content/updates.txt", "Add news"),
    ("content/publications.yaml", "Update publications"),
    ("content/", "Update page content"),
    ("static/", "Update files"),
    ("config.yaml", "Update site settings"),
    ("templates/", "Update layout"),
)


def git(*args, check=True):
    """Run git in the repository and return its stdout."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def suggested_message(paths):
    """Describe the changed paths in a short commit message."""
    parts = []
    for path in paths:
        for prefix, phrase in MESSAGE_HINTS:
            if path.startswith(prefix):
                if phrase not in parts:
                    parts.append(phrase)
                break
        else:
            if "Update site" not in parts:
                parts.append("Update site")
    return "; ".join(parts) or "Update site"


def changed_paths():
    """Paths with uncommitted changes (ignored files such as docs/ excluded)."""
    lines = git("status", "--porcelain", "--untracked-files=all").splitlines()
    return [line[3:].split(" -> ")[-1].strip('"') for line in lines if line]


def publish(output_dir):
    """Lint and build, then commit all changes and push them to GitHub."""
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch != BRANCH:
        raise SystemExit(
            f"You are on '{branch}'; only '{BRANCH}' is deployed. "
            f"Switch with: git switch {BRANCH}"
        )
    print("Checking GitHub for newer changes...")
    git("fetch", "--quiet", "origin", BRANCH)
    behind = int(git("rev-list", "--count", f"HEAD..origin/{BRANCH}").strip())
    if behind:
        raise SystemExit(
            f"GitHub has {behind} commit(s) you don't have yet. "
            "Run `git pull --rebase` first, then publish again."
        )

    run_lint()
    print("Building the site...")
    build(load_config(), output_dir)
    print("Build OK; all local links resolve.\n")

    paths = changed_paths()
    ahead = int(git("rev-list", "--count", f"origin/{BRANCH}..HEAD").strip())
    try:
        if not paths:
            if not ahead:
                print("Nothing to publish: no changes and nothing unpushed.")
                return
            print(f"No new changes, but {ahead} commit(s) are not on GitHub yet.")
            if not confirm("Push them now?"):
                raise Cancelled
        else:
            print("These changes will be published:")
            print(git("status", "--short", "--untracked-files=all").rstrip())
            print()
            message = ask(
                "Commit message", default=suggested_message(paths), required=True
            )
            if not confirm(f'Commit {len(paths)} file(s) as "{message}" and push?'):
                raise Cancelled
            git("add", "--all")
            git("commit", "--quiet", "-m", message)
    except Cancelled:
        print("Cancelled; nothing was committed or pushed.")
        return

    print("Pushing to GitHub...")
    git("push", "--quiet", "origin", BRANCH)
    commit = git("rev-parse", "--short", "HEAD").strip()
    print(f"Published {commit}. The site updates in about a minute; follow it at")
    print(f"  {ACTIONS_URL}")
