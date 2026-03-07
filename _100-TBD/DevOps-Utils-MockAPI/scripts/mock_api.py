import os
import sys
import json
import argparse
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


def _load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    # Build route lookup: (METHOD, path) -> route
    routes = {}
    for route in spec.get("routes", []):
        key = (route["method"].upper(), route["path"])
        routes[key] = route
    return spec, routes


def _make_handler(routes: dict, cors: bool, verbose: bool):
    class MockHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            if verbose:
                print(f"  → {self.command} {self.path} — {args[1] if len(args) > 1 else ''}")

        def _send(self, status: int, body, extra_headers: dict = None):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            if cors:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def _handle(self):
            parsed = urlparse(self.path)
            key = (self.command, parsed.path)
            route = routes.get(key)
            if route:
                self._send(route.get("status", 200), route.get("body", {}))
            else:
                self._send(404, {"error": "Not found", "path": parsed.path, "method": self.command})

        def do_OPTIONS(self):
            if cors:
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.end_headers()
            else:
                self._handle()

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

    return MockHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight local mock REST API server.")
    parser.add_argument("--spec",    required=True, help="Path to JSON spec file")
    parser.add_argument("--port",    type=int, default=3000)
    parser.add_argument("--cors",    action="store_true", help="Add CORS headers")
    parser.add_argument("--verbose", action="store_true", help="Log all requests")
    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f"Error: spec file '{args.spec}' not found."); sys.exit(1)

    spec, routes = _load_spec(args.spec)
    port = spec.get("port", args.port)

    print(f"🚀  Mock API server running on http://localhost:{port}")
    print(f"    Spec: {args.spec}   CORS: {'on' if args.cors else 'off'}")
    for (method, path), route in sorted(routes.items()):
        print(f"    {method:6s} {path}  →  {route.get('status', 200)}")
    print("    Ctrl-C to stop\n")

    handler = _make_handler(routes, args.cors, args.verbose)
    server = HTTPServer(("", port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
