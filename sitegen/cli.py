"""Command-line interface: sitegen init|add-news|add-paper|lint|build|serve|publish."""

import argparse
from pathlib import Path

from .add import add_news, add_paper
from .build import build
from .config import ROOT, load_config
from .init import init
from .lint import run_lint
from .publish import publish
from .render import clean
from .serve import serve


def main():
    parser = argparse.ArgumentParser(
        prog="sitegen",
        description="Static site generator for a personal website.",
    )
    parser.add_argument(
        "commands",
        nargs="*",
        default=["build"],
        choices=[
            "init",
            "add-news",
            "add-paper",
            "lint",
            "clean",
            "build",
            "serve",
            "publish",
        ],
        help="Commands to run in sequence: 'init' creates a new site in the "
        "current folder (run it on its own); 'add-news' and 'add-paper' ask "
        "questions interactively; then 'lint', 'clean', 'build', 'serve'; "
        "'publish' builds, commits and pushes",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "docs",
        help="Output directory for the built site (default: docs)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port for 'serve' (default: 8000)",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Commit message for 'publish' (default: ask, suggesting one)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Don't ask questions: 'publish' commits and pushes, 'init' uses "
        "the suggested name, email and URL",
    )
    args = parser.parse_args()
    if "init" in args.commands:
        if args.commands != ["init"]:
            raise SystemExit("Run 'init' on its own, then the other commands.")
        init(yes=args.yes)
        return
    if not (ROOT / "config.yaml").is_file():
        raise SystemExit(
            f"No config.yaml in {ROOT} or any folder above it. "
            "Run sitegen from inside your site's folder."
        )

    for cmd in args.commands:
        if cmd == "add-news":
            add_news()
        elif cmd == "add-paper":
            add_paper()
        elif cmd == "lint":
            issues = run_lint()
            print(f"Config OK ({len(issues)} warning(s)).")
        elif cmd == "clean":
            print("Cleaning up generated files...")
            clean(args.output)
        elif cmd == "build":
            run_lint()
            print("Generating HTML files...")
            build(load_config(), args.output)
            print(f"Built {args.output}; all local links resolve.")
        elif cmd == "serve":
            serve(args.output, args.port)
        elif cmd == "publish":
            publish(args.output, message=args.message, yes=args.yes)
