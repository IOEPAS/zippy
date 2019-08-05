"""Serve static files as well as json-like logs to json."""
import http.server
import os
import pathlib
import socketserver

from zippy.utils.json_generator import write_json_output

PORT = 3000

ROOT_DIR = (pathlib.Path(__file__).parent / "..").resolve()
PUBLIC_DIR = ROOT_DIR / "public"
LOG_FILE = ROOT_DIR / "output" / "logs" / "display" / "output.log"

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


class RequestHandler(CORSRequestHandler):
    """Request Handler that serves log file in json output as well as complete directory."""

    def do_GET(self):
        """Return GET response."""
        if not self.path.startswith("/logs"):
            super().do_GET()
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        with open(LOG_FILE, "rb") as file:
            write_json_output(file, self.wfile)


# Python 3.7 has ThreadingHTTPServer that does this already
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server."""


if __name__ == "__main__":
    with ThreadingHTTPServer(("", PORT), RequestHandler) as httpd:
        LOG_FILE.touch()
        print("Started json server on port ", PORT)
        httpd.serve_forever()
