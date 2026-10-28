"""Responsive images: WebP copies in several widths for each local photo."""

import re

from PIL import Image

# Widths (in pixels) of the WebP copies; the original width is always added.
IMAGE_WIDTHS = (320, 640, 960, 1280)
WEBP_QUALITY = 80
# Display width of content images: full width on phones, else the 760px column.
DEFAULT_SIZES = "(max-width: 760px) 100vw, 760px"

IMG_RE = re.compile(r"<img\b[^>]*>")
SRC_RE = re.compile(r'\bsrc="(images/[^"?]+\.(?:jpe?g|png))(\?[^"]*)?"', re.I)
SIZES_RE = re.compile(r'\bsizes="([^"]*)"')


def webp_variants(output_dir, path, cache):
    """Write WebP copies of `path` (relative to output_dir); return (url, width)."""
    if path not in cache:
        source = output_dir / path
        with Image.open(source) as image:
            image = image.convert(
                "RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB"
            )
            widths = [w for w in IMAGE_WIDTHS if w < image.width] + [image.width]
            variants = []
            for width in widths:
                height = round(image.height * width / image.width)
                name = f"{source.stem}-{width}.webp"
                image.resize((width, height), Image.LANCZOS).save(
                    source.with_name(name), "WEBP", quality=WEBP_QUALITY
                )
                variants.append((f"{path.rsplit('/', 1)[0]}/{name}", width))
        cache[path] = variants
    return cache[path]


def picture(output_dir, img_tag, cache):
    """Wrap a local JPEG/PNG <img> in a <picture> offering WebP copies."""
    match = SRC_RE.search(img_tag)
    if not match:
        return img_tag  # external image, SVG, or already WebP
    path, query = match.group(1), match.group(2) or ""
    srcset = ", ".join(
        f"{url}{query} {width}w"
        for url, width in webp_variants(output_dir, path, cache)
    )
    sizes_match = SIZES_RE.search(img_tag)
    sizes = sizes_match.group(1) if sizes_match else DEFAULT_SIZES
    return (
        f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
        f"{img_tag}</picture>"
    )


def add_responsive_images(output_dir, html_paths):
    """Rewrite each page so its local photos are served as sized WebP."""
    cache = {}
    for html_path in html_paths:
        html = html_path.read_text()
        html_path.write_text(
            IMG_RE.sub(lambda m: picture(output_dir, m.group(0), cache), html)
        )
    print(f"\tWriting WebP copies of {len(cache)} image(s)")
