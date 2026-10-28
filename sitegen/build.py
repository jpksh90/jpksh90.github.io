"""Building the site atomically: the output folder changes only on success."""

import shutil
import tempfile
from pathlib import Path

from .links import broken_links
from .render import OUTPUT_MARKER, generate

# Prefix of the hidden staging folders created next to the output folder.
STAGING_PREFIX = ".sitegen-staging-"


def is_replaceable(output_dir):
    """True if `output_dir` is missing, empty, or was created by build."""
    if not output_dir.exists():
        return True
    if output_dir.is_file():
        return False
    return (output_dir / OUTPUT_MARKER).is_file() or not any(output_dir.iterdir())


def build(config, output_dir):
    """Build the site into a staging folder, check it, then swap it in.

    If rendering or the link check fails, the staging folder is deleted and
    `output_dir` is left exactly as it was. An existing `output_dir` is only
    replaced if a previous build created it (it holds OUTPUT_MARKER).
    """
    output_dir = output_dir.resolve()
    if not is_replaceable(output_dir):
        raise SystemExit(
            f"Refusing to replace {output_dir}: it was not created by build. "
            "Remove it or choose another folder with -o."
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    # Stage next to the output so the final rename stays on one filesystem.
    old_dir = None
    staging_dir = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=output_dir.parent))
    try:
        written = generate(config, staging_dir)
        problems = broken_links(staging_dir, written)
        if problems:
            raise SystemExit(
                f"Broken links found; {output_dir.name}/ was not changed:\n\t"
                + "\n\t".join(problems)
            )
        if output_dir.exists():
            old_dir = output_dir.with_name(f"{STAGING_PREFIX}old-{output_dir.name}")
            shutil.rmtree(old_dir, ignore_errors=True)
            output_dir.rename(old_dir)
        staging_dir.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        # If the swap failed halfway, put the previous site back.
        if old_dir is not None and old_dir.exists() and not output_dir.exists():
            old_dir.rename(output_dir)
        raise
    if old_dir is not None:
        shutil.rmtree(old_dir)
