"""Local preview server."""

import contextlib
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def serve(output_dir, port):
    """Serve the output directory for local preview."""
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(output_dir))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {output_dir} at http://localhost:{port}/ (Ctrl+C to stop)")
        with contextlib.suppress(KeyboardInterrupt):
            server.serve_forever()
