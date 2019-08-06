"""Serve static files as well as json-like logs to json."""
import http.server
import os
import pathlib
import socketserver

from http import HTTPStatus
from urllib.parse import urlparse

from zippy.utils.json_generator import write_json_output

PORT = 3000

ROOT_DIR = (pathlib.Path(__file__).parent / "..").resolve()
PUBLIC_DIR = ROOT_DIR / "public"
LOG_DIR = ROOT_DIR / "output" / "logs" / "display"
LOG_FILE = LOG_DIR / "output.log"

# Python3.7 has directory class attribute inside `SimpleHTTPRequestHandler`
# but, to be compatible with 3.6, let's chdir into directory
os.chdir(PUBLIC_DIR)


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Enable CORS on all domains."""

    CORS_HEADER = ("Access-Control-Allow-Origin", "*")

    def end_headers(self):
        """Return CORS header."""
        self.send_header(*self.CORS_HEADER)
        super().end_headers()


class JSONLogRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Return json log."""

    def do_json(self):
        """Return json log with appropriate headers."""
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        with open(LOG_FILE, "rb") as file:
            write_json_output(file, self.wfile)


class RequestHandler(JSONLogRequestHandler, CORSRequestHandler):
    """Request Handler that serves log file in json output as well as complete directory."""

    def do_GET(self):
        """Return GET response."""
        url = urlparse(self.path)
        if url.path == "/logs":
            self.do_json()
            return

        super().do_GET()


# Python 3.7 has ThreadingHTTPServer that does this already
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server."""


if __name__ == "__main__":
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch()

    with ThreadingHTTPServer(("", PORT), RequestHandler) as httpd:
        print("Started json server on port", PORT)
        httpd.serve_forever()
