"""Command-line interface: site-utils.py lint|clean|build|serve."""

import argparse
from pathlib import Path

from .build import build
from .config import ROOT, load_config
from .lint import run_lint
from .render import clean
from .serve import serve


def main():
    parser = argparse.ArgumentParser(
        description="Static site generator for personal website."
    )
    parser.add_argument(
        "commands",
        nargs="*",
        default=["build"],
        choices=["lint", "clean", "build", "serve"],
        help="Commands to run in sequence: 'lint', 'clean', 'build', 'serve'",
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
    args = parser.parse_args()

    for cmd in args.commands:
        if cmd == "lint":
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
