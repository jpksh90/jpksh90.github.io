"""Build the site: uv run site-utils.py [lint] [clean] [build] [serve].

The generator lives in the sitegen/ package; see README.md.
"""

from sitegen.cli import main

if __name__ == "__main__":
    main()
