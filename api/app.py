"""REST API over the MoMo SMS dataset, secured with HTTP Basic Authentication.

Run:  python3 api/app.py          (listens on http://localhost:8000)
"""

import base64
import binascii
import hmac
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsa.parse_xml import load_transactions  # noqa: E402

USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "momo2025")
HOST = os.environ.get("API_HOST", "localhost")
PORT = int(os.environ.get("API_PORT", "8000"))

ID_ROUTE = re.compile(r"^/transactions/(\d+)/?$")
LIST_ROUTE = re.compile(r"^/transactions/?$")

# id -> transaction. A dictionary keeps every lookup O(1); see dsa/dsa_comparison.py.
class _State:
    store: dict = None
    next_id: int = 1

    def __init__(self):
        self.store = {}
        self.next_id = 1

_state = _State()

EDITABLE_FIELDS = (
    "transaction_type", "amount", "fee", "new_balance", "sender", "sender_phone",
    "receiver", "receiver_phone", "receiver_code", "account",
    "financial_transaction_id", "timestamp", "readable_date",
    "service_center", "address", "body",
)
REQUIRED_FIELDS = ("transaction_type", "amount")


def bootstrap():
    """Load the parsed dataset into the in-memory store."""
    for record in load_transactions():
        _state.store[record["id"]] = record
    _state.next_id = max(_state.store) + 1 if _state.store else 1


def validate(payload, partial=False):
    """Return (cleaned_record, error_message)."""
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object"

    unknown = set(payload) - set(EDITABLE_FIELDS)
    if unknown:
        return None, f"Unknown field(s): {', '.join(sorted(unknown))}"

    if not partial:
        missing = [f for f in REQUIRED_FIELDS if f not in payload]
        if missing:
            return None, f"Missing required field(s): {', '.join(missing)}"

    cleaned = dict(payload)
    for field in ("amount", "fee", "new_balance"):
        if field in cleaned and cleaned[field] is not None:
            if isinstance(cleaned[field], bool) or not isinstance(cleaned[field], (int, float)):
                return None, f"Field '{field}' must be a number"
            if cleaned[field] < 0:
                return None, f"Field '{field}' cannot be negative"
            cleaned[field] = float(cleaned[field])

    if "transaction_type" in cleaned and not str(cleaned["transaction_type"]).strip():
        return None, "Field 'transaction_type' cannot be empty"

    return cleaned, None


class TransactionHandler(BaseHTTPRequestHandler):
    server_version = "MoMoAPI/1.0"

    # ---------- helpers ----------

    def send_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, message):
        self.send_json(status, {"error": message, "status": status})

    def unauthorized(self, message="Unauthorized: valid credentials required"):
        body = json.dumps({"error": message, "status": 401}, indent=2).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo Transactions API"')
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authenticated(self):
        """Verify the Authorization header; send a 401 and return False when invalid."""
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            self.unauthorized("Unauthorized: missing Basic Authentication credentials")
            return False
        try:
            decoded = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
            user, _, password = decoded.partition(":")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            self.unauthorized("Unauthorized: malformed Authorization header")
            return False

        # compare_digest keeps the check constant-time against timing attacks
        ok_user = hmac.compare_digest(user, USERNAME)
        ok_password = hmac.compare_digest(password, PASSWORD)
        if not (ok_user and ok_password):
            self.unauthorized("Unauthorized: invalid username or password")
            return False
        return True

    def read_json_body(self):
        """Return (payload, error_message)."""
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None, "Invalid Content-Length header"
        if length <= 0:
            return None, "Request body is required"
        try:
            return json.loads(self.rfile.read(length).decode("utf-8")), None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, "Request body must be valid JSON"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ---------- routes ----------

    def do_GET(self):
        if not self.authenticated():
            return

        if LIST_ROUTE.match(self.path.split("?")[0]):
            records = sorted(_state.store.values(), key=lambda r: r["id"])
            self.send_json(200, {"count": len(records), "transactions": records})
            return

        match = ID_ROUTE.match(self.path)
        if match:
            record = _state.store.get(int(match.group(1)))
            if record is None:
                self.send_error_json(404, f"Transaction {match.group(1)} not found")
                return
            self.send_json(200, record)
            return

        self.send_error_json(404, f"Unknown endpoint: {self.path}")

    def do_POST(self):
        if not self.authenticated():
            return
        if not LIST_ROUTE.match(self.path):
            self.send_error_json(404, f"Unknown endpoint: {self.path}")
            return

        payload, error = self.read_json_body()
        if error:
            self.send_error_json(400, error)
            return
        cleaned, error = validate(payload)
        if error:
            self.send_error_json(400, error)
            return

        record = {"id": _state.next_id}
        record.update({field: None for field in EDITABLE_FIELDS})
        record.update(cleaned)
        _state.store[_state.next_id] = record
        _state.next_id += 1

        self.send_json(201, record)

    def do_PUT(self):
        if not self.authenticated():
            return
        match = ID_ROUTE.match(self.path)
        if not match:
            self.send_error_json(404, f"Unknown endpoint: {self.path}")
            return

        record_id = int(match.group(1))
        if record_id not in _state.store:
            self.send_error_json(404, f"Transaction {record_id} not found")
            return

        payload, error = self.read_json_body()
        if error:
            self.send_error_json(400, error)
            return
        cleaned, error = validate(payload, partial=True)
        if error:
            self.send_error_json(400, error)
            return

        _state.store[record_id].update(cleaned)
        self.send_json(200, _state.store[record_id])

    def do_DELETE(self):
        if not self.authenticated():
            return
        match = ID_ROUTE.match(self.path)
        if not match:
            self.send_error_json(404, f"Unknown endpoint: {self.path}")
            return

        record_id = int(match.group(1))
        if record_id not in _state.store:
            self.send_error_json(404, f"Transaction {record_id} not found")
            return

        deleted = _state.store.pop(record_id)
        self.send_json(200, {"message": f"Transaction {record_id} deleted", "deleted": deleted})


def main():
    bootstrap()
    server = HTTPServer((HOST, PORT), TransactionHandler)
    print(f"Loaded {len(_state.store)} transactions")
    print(f"Serving on http://{HOST}:{PORT}  (user: {USERNAME})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")
        server.server_close()


if __name__ == "__main__":
    main()
