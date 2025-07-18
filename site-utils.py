import argparse
from jinja2 import Environment, FileSystemLoader
import markdown
import os

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('base.html')


pages = [
    "index",
    "publications",
    "research",
    "teaching",
    # "contact"
]

def clean_pages(pages, output_dir):
    """Remove generated HTML files for the given pages."""
    for page in pages:
        html_file = os.path.join(output_dir, f"{page}.html")
        if os.path.exists(html_file):
            os.remove(html_file)
            print(f"\tDeleted {html_file}")

def generate(output_dir):
    for page in pages:
        with open(f"content/{page}.md") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=['extra'])
        rendered = template.render(content=html_content, page=f"{page}.html")
        html_path = os.path.join(output_dir, f"{page}.html")
        with open(html_path, "w") as f:
            print(f"\tRendering {page}.html")
            f.write(rendered)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Static site generator for personal website.")
    parser.add_argument("commands", nargs="*", default=["build"], choices=["clean", "build"],
                        help="Commands to run: 'build', 'clean', or both in sequence")
    parser.add_argument("-o", "--output", default="docs",
                        help="Output directory for generated HTML files (default: docs)")
    args = parser.parse_args()

    for cmd in args.commands:
        if cmd == "clean":
            print("Cleaning up old HTML files...")
            clean_pages(pages, output_dir=args.output)
        elif cmd == "build":
            print("Generating HTML files...")
            generate(output_dir=args.output)
            print("HTML files generated successfully.")

