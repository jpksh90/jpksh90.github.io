"""`sitegen publish`: check, build, commit and push the site in one step."""

import re
import subprocess

from .add import Cancelled, ask, confirm
from .build import build
from .config import ROOT, load_config
from .lint import run_lint

# owner/repo in a GitHub remote: https://github.com/o/r.git or git@github.com:o/r
GITHUB_REMOTE_RE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")

# Suggested commit message parts, by the first changed path that matches.
MESSAGE_HINTS = (
    ("content/updates.txt", "Add news"),
    ("content/publications.yaml", "Update publications"),
    ("content/", "Update page content"),
    ("static/", "Update files"),
    ("config.yaml", "Update site settings"),
    ("templates/", "Update layout"),
)


def git(*args, check=True, cwd=ROOT):
    """Run git in the repository and return its stdout."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def github_repo(cwd=ROOT):
    """Return (owner, repo) of the GitHub `origin` remote, or None."""
    match = GITHUB_REMOTE_RE.search(
        git("remote", "get-url", "origin", check=False, cwd=cwd).strip()
    )
    return match.groups() if match else None


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


def publish(output_dir, message=None, yes=False):
    """Lint and build, then commit all changes and push them to `origin`.

    `message` replaces the suggested commit message and `yes` answers every
    question with yes, so it can run without prompts.
    """
    run_lint()
    config = load_config()
    target = config["branch"]
    # Unlike rev-parse, this also works before the first commit.
    branch = git("branch", "--show-current").strip()
    if branch != target:
        raise SystemExit(
            f"You are on '{branch}'; only '{target}' is deployed. "
            f"Switch with: git switch {target}"
        )
    print("Checking origin for newer changes...")
    # False on the first publish, before the branch exists on origin.
    on_remote = bool(git("ls-remote", "--heads", "origin", target).strip())
    if on_remote:
        git("fetch", "--quiet", "origin", target)
        behind = int(git("rev-list", "--count", f"HEAD..origin/{target}").strip())
    else:
        behind = 0
    if behind:
        raise SystemExit(
            f"origin has {behind} commit(s) you don't have yet. "
            "Run `git pull --rebase` first, then publish again."
        )

    print("Building the site...")
    build(config, output_dir)
    print("Build OK; all local links resolve.\n")

    paths = changed_paths()
    unpushed = f"origin/{target}..HEAD" if on_remote else "HEAD"
    # check=False: before the first commit there is no HEAD to count from.
    ahead = int(git("rev-list", "--count", unpushed, check=False).strip() or 0)
    try:
        if not paths:
            if not ahead:
                print("Nothing to publish: no changes and nothing unpushed.")
                return
            print(f"No new changes, but {ahead} commit(s) are not pushed yet.")
            if not (yes or confirm("Push them now?")):
                raise Cancelled
        else:
            print("These changes will be published:")
            print(git("status", "--short", "--untracked-files=all").rstrip())
            print()
            if not message:
                default = suggested_message(paths)
                message = default if yes else ask("Commit message", default, True)
            question = f'Commit {len(paths)} file(s) as "{message}" and push?'
            if not (yes or confirm(question)):
                raise Cancelled
            git("add", "--all")
            git("commit", "--quiet", "-m", message)
    except Cancelled:
        print("Cancelled; nothing was committed or pushed.")
        return

    print("Pushing...")
    git("push", "--quiet", "--set-upstream", "origin", target)
    commit = git("rev-parse", "--short", "HEAD").strip()
    repo = github_repo()
    if repo:
        print(f"Published {commit}. The site updates in about a minute; follow it at")
        print(f"  https://github.com/{repo[0]}/{repo[1]}/actions")
    else:
        print(f"Published {commit}.")
