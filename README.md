# MoMo SMS REST API

A secured REST API over MTN Mobile Money SMS records. The project parses an XML SMS export into
JSON, serves it through CRUD endpoints protected by HTTP Basic Authentication, and benchmarks two
search strategies (linear search vs. dictionary lookup) over the parsed data.

**Dataset:** 1,691 SMS records parsed from `data/modified_sms_v2.xml`.

---

## Repository layout

```
.
├── api/
│   └── app.py                  # REST API (http.server) with Basic Auth + CRUD
├── dsa/
│   ├── parse_xml.py            # XML -> JSON transaction parser
│   └── dsa_comparison.py       # Linear search vs dictionary lookup benchmark
├── data/
│   ├── modified_sms_v2.xml     # Source dataset
│   └── transactions.json       # Generated parser output
├── docs/
│   ├── api_docs.md             # Full endpoint documentation
│   ├── security_notes.md       # Basic Auth limitations & stronger alternatives
│   ├── report.pdf              # Written report (PDF deliverable)
│   └── build_report.py         # Regenerates report.pdf from the captured results
├── screenshots/
│   ├── run_tests.sh            # curl test suite covering every endpoint
│   ├── api_test_results.txt    # Captured request/response transcript
│   └── dsa_results.txt         # Captured benchmark output
└── README.md
```

---

## Requirements

Python 3.8 or newer. No third-party packages — the API uses only the standard library
(`http.server`, `xml.etree.ElementTree`, `base64`, `hmac`, `json`).

---

## Setup

```bash
git clone https://github.com/Chol1000/dema3.git
cd dema3
```

### 1. Parse the XML into JSON

```bash
python3 dsa/parse_xml.py
```

Writes `data/transactions.json` and prints a per-category summary:

```
Parsed 1691 SMS records -> data/transactions.json

Records per transaction type:
  payment_to_code_holder     658
  transfer_to_mobile         585
  bank_deposit               249
  incoming_money             63
  bill_or_airtime_payment    53
  third_party_payment        36
  ...
```

### 2. Start the API

```bash
python3 api/app.py
```

```
Loaded 1691 transactions
Serving on http://localhost:8000  (user: admin)
```

Credentials default to `admin` / `momo2025` and can be overridden:

```bash
API_USERNAME=myuser API_PASSWORD=mysecret API_PORT=9000 python3 api/app.py
```

### 3. Run the DSA benchmark

```bash
python3 dsa/dsa_comparison.py
```

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/transactions` | List all transactions |
| `GET` | `/transactions/{id}` | Retrieve one transaction |
| `POST` | `/transactions` | Create a transaction |
| `PUT` | `/transactions/{id}` | Update a transaction |
| `DELETE` | `/transactions/{id}` | Delete a transaction |

All endpoints require Basic Authentication. Full request/response examples and error codes are in
[`docs/api_docs.md`](docs/api_docs.md).

### Quick examples

```bash
# List all
curl -u admin:momo2025 http://localhost:8000/transactions

# One record
curl -u admin:momo2025 http://localhost:8000/transactions/1

# Wrong password -> 401
curl -i -u admin:wrongpassword http://localhost:8000/transactions

# Create
curl -u admin:momo2025 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_type":"incoming_money","amount":7500,"sender":"Chol Deng"}'

# Update
curl -u admin:momo2025 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" -d '{"amount":9900}'

# Delete
curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692
```

---

## Testing

With the server running in another terminal:

```bash
bash screenshots/run_tests.sh
```

This exercises all nine cases — authenticated GET (list and by id), wrong password, missing
credentials, POST, PUT, DELETE, GET on a deleted record, and an invalid POST body. The captured
transcript is in [`screenshots/api_test_results.txt`](screenshots/api_test_results.txt).

---

## DSA results

Linear search vs. dictionary lookup across 20 ids spread over all 1,691 records, 1,000 repeats each:

| Target position | Linear search (µs) | Dictionary lookup (µs) | Speed-up |
|---|---|---|---|
| 1 | 0.082 | 0.065 | 1.3× |
| 421 | 10.153 | 0.065 | 156.6× |
| 841 | 20.365 | 0.065 | 313.7× |
| 1261 | 30.565 | 0.063 | 481.7× |
| 1597 | 38.320 | 0.065 | 591.8× |
| **Average** | **19.238** | **0.065** | **297.1×** |

Linear search costs grow linearly with how deep the record sits in the list — **O(n)**. Dictionary
lookup stays flat at roughly 0.065 µs regardless of position — **O(1)** — because Python hashes the
key directly to its bucket instead of comparing records one by one. On this dataset that is about a
**297× average speed-up**.

Other options that would improve on linear search:

- **Binary search** on an id-sorted list — **O(log n)**, needs no extra memory beyond the sorted
  order, but requires the list to stay sorted.
- **B-tree / database index** — how a real database indexes a primary key; keeps lookups fast while
  also supporting range queries such as "all transactions between two dates".
- **Hash index on secondary fields** (e.g. `sender`, `transaction_type`) — extends O(1) lookups
  beyond the primary key.

The API itself stores transactions in a dictionary keyed by id, so every `GET`, `PUT` and `DELETE`
by id is an O(1) operation.

Full output: [`screenshots/dsa_results.txt`](screenshots/dsa_results.txt).

---

## Report

The written report is at [`docs/report.pdf`](docs/report.pdf). It covers the introduction to API
security, endpoint documentation, the DSA comparison results and the reflection on Basic Auth
limitations. Regenerate it after re-running the benchmark with:

```bash
python3 docs/build_report.py
```

---

## Security

Basic Auth only base64-encodes credentials — it is encoding, not encryption — so it is weak on its
own. See [`docs/security_notes.md`](docs/security_notes.md) for the limitations and stronger
alternatives (JWT, OAuth 2.0).
