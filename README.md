# MoMo SMS REST API

This project takes an SMS backup from an MTN Mobile Money account, turns it into JSON, and serves it
through a small REST API. Every endpoint is protected with Basic Authentication. We also compared
two ways of finding a record by id (linear search and a dictionary) to see which one is faster.

The dataset has 1,691 SMS records and comes from `data/modified_sms_v2.xml`.

---

## Repository layout

```
.
├── api/
│   ├── __init__.py
│   └── app.py                  # The REST API (http.server) with Basic Auth
├── dsa/
│   ├── __init__.py
│   ├── parse_xml.py            # Turns the XML into JSON
│   └── dsa_comparison.py       # Linear search vs dictionary benchmark
├── data/
│   ├── modified_sms_v2.xml     # The SMS backup we were given
│   └── transactions.json       # What the parser produces
├── docs/
│   ├── api_docs.md             # Documentation for every endpoint
│   ├── security_notes.md       # Why Basic Auth is weak, and what to use instead
│   ├── report.pdf              # The written report
│   └── build_report.py         # Script that generates report.pdf
├── screenshots/
│   ├── run_tests.sh            # curl tests for every endpoint
│   ├── api_test_results.txt    # Saved output of those tests
│   └── dsa_results.txt         # Saved output of the benchmark
├── check_submission.py         # Checks nothing is missing before submitting
├── requirements.txt
└── README.md
```

---

## Where each task lives

The assignment has six tasks. This is where each one is:

| Task | Where |
|---|---|
| 1. Data parsing | `dsa/parse_xml.py`, output in `data/transactions.json` |
| 2. CRUD endpoints | `api/app.py` |
| 3. Authentication and security | `api/app.py`, written up in `docs/security_notes.md` |
| 4. API documentation | `docs/api_docs.md` |
| 5. Linear search vs dictionary | `dsa/dsa_comparison.py`, output in `screenshots/dsa_results.txt` |
| 6. Testing | `screenshots/run_tests.sh`, output in `screenshots/api_test_results.txt` |

The parser sits in `dsa/` rather than at the top level because the assignment
asks for "XML parsing & DSA code (dsa/ folder)".

---

## What you need

Python 3.8 or newer. The parser, the API, the benchmark and the tests all run on the standard
library alone, so there is nothing to install to use the project.

The only extra package is `reportlab`, and it is only needed if you want to rebuild the PDF report:

```bash
pip install -r requirements.txt
```

---

## Getting it running

```bash
git clone https://github.com/Chol1000/dema3.git
cd dema3
```

### Step 1 — turn the XML into JSON

```bash
python3 dsa/parse_xml.py
```

This writes `data/transactions.json` and prints a summary of what it found:

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

Here is one record from the output, so you can see the shape of it:

```json
{
  "id": 1,
  "transaction_type": "incoming_money",
  "amount": 2000.0,
  "fee": null,
  "new_balance": 2000.0,
  "sender": "Jane Smith",
  "sender_phone": "*********013",
  "receiver": null,
  "receiver_phone": null,
  "receiver_code": null,
  "account": null,
  "financial_transaction_id": "76662021700",
  "timestamp": "2024-05-10T16:30:51",
  "readable_date": "10 May 2024 4:30:58 PM",
  "service_center": "+250788110381",
  "address": "M-Money",
  "body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile ..."
}
```

Plenty of the fields are null on any given record and that is normal. This one
is money coming in, so it has a sender but no receiver. An outgoing payment is
the other way round. The parser only fills in what the SMS actually says.

### Step 2 — start the API

```bash
python3 api/app.py
```

```
Loaded 1691 transactions
Serving on http://localhost:8000  (user: admin)
```

The login is `admin` / `momo2025` by default. You can change it without touching the code:

```bash
API_USERNAME=myuser API_PASSWORD=mysecret API_PORT=9000 python3 api/app.py
```

Those defaults are only there so the project runs straight after cloning. They are
not a secret, they are printed in this README, and anything real should set
`API_USERNAME` and `API_PASSWORD` instead. The server also listens on `localhost`
only, so nothing outside your own machine can reach it.

### Step 3 — run the benchmark

```bash
python3 dsa/dsa_comparison.py
```

This one takes about 30 seconds because it repeats each measurement a thousand times.
It prints how far along it is as it goes, so you can tell it has not frozen.

---

## The endpoints

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/transactions` | Lists every transaction |
| `GET` | `/transactions/{id}` | Gets one transaction |
| `POST` | `/transactions` | Adds a new one |
| `PUT` | `/transactions/{id}` | Updates one |
| `DELETE` | `/transactions/{id}` | Deletes one |

All of them need a username and password. Full examples, responses and error codes are in
[`docs/api_docs.md`](docs/api_docs.md).

Some quick ones to try:

```bash
# Everything
curl -u admin:momo2025 http://localhost:8000/transactions

# Just one record
curl -u admin:momo2025 http://localhost:8000/transactions/1

# Wrong password, so you get a 401 back
curl -i -u admin:wrongpassword http://localhost:8000/transactions

# Add a record
curl -u admin:momo2025 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_type":"incoming_money","amount":7500,"sender":"Chol Deng"}'

# Change it
curl -u admin:momo2025 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" -d '{"amount":9900}'

# Remove it
curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692
```

---

## Testing

Start the server in one terminal, then in another run:

```bash
bash screenshots/run_tests.sh
```

It goes through nine cases: listing all transactions, getting one by id, using a wrong password,
sending no password at all, creating a record, updating it, deleting it, asking for it again after
it is gone, and finally posting a bad request body. Each one prints its status code so you can see
what happened. The saved output is in
[`screenshots/api_test_results.txt`](screenshots/api_test_results.txt).

The script reads the new id out of the POST response instead of assuming what it will be, so you can
run it as many times as you like against the same server.

There is also a checklist script that looks over the whole repo and tells you if anything the
assignment asks for is missing:

```bash
python3 check_submission.py
```

It checks the parsed JSON has the key fields, that all four HTTP methods are handled, that the
security notes cover JWT and OAuth 2.0, that every endpoint is documented with examples and error
codes, that at least 20 records were benchmarked, that the screenshots are there, and that more than
one person has committed. It does not test the running API, so use `run_tests.sh` for that.

---

## Which search is faster?

We tested both methods on 20 different ids spread across all 1,691 records, repeating each
measurement 1,000 times.

| Position in the list | Linear search (µs) | Dictionary (µs) | Speed-up | Linear comparisons | Dictionary comparisons |
|---|---|---|---|---|---|
| 1 | 0.079 | 0.063 | 1.3× | 1 | 1 |
| 421 | 10.207 | 0.065 | 158.0× | 421 | 1 |
| 841 | 20.464 | 0.062 | 328.5× | 841 | 1 |
| 1261 | 30.529 | 0.064 | 476.1× | 1261 | 1 |
| 1597 | 39.065 | 0.063 | 616.8× | 1597 | 1 |
| **Average** | **19.355** | **0.064** | **304.5×** | **799.0** | **1.0** |

The dictionary won by about 304 times on average.

**Why is the dictionary faster?** Because it does not actually search. Linear search starts at the
beginning of the list and checks records one by one until it finds the right id, so a record near
the end costs far more than one near the start. You can see that in the table: the first record
needs 1 comparison, but a record at position 1,597 needs 1,597 of them. That is O(n).

A dictionary works differently. Python runs the id through a hash function, and the result tells it
exactly where the value is stored, so it goes straight there. That is one comparison whether the
dictionary holds ten records or ten thousand, which is O(1).

The comparison counts are worth paying attention to because they do not depend on the computer. A
faster laptop would make both time columns smaller, but linear search would still need 1,597
comparisons and the dictionary would still need 1. The gap is in how the two methods work, not in
how fast the machine is.

The catch is that you have to build the dictionary first, which costs one pass through the data and
some extra memory. You pay that once and get it back on every lookup after that. That is why the API
keeps its records in a dictionary, so getting, updating or deleting by id is O(1).

**What else could work?** A few options:

- **Binary search** on a list sorted by id. That is O(log n) because each step throws away half of
  what is left. It needs no extra memory, but the list has to stay sorted.
- **A B-tree, or a normal database index.** This is what a real database uses for a primary key. It
  stays fast and it can also answer range questions a dictionary cannot, like "every transaction
  between these two dates".
- **A second dictionary on another field**, say `sender` or `transaction_type`, if you need fast
  lookups on something other than the id.

The full output is in [`screenshots/dsa_results.txt`](screenshots/dsa_results.txt).

---

## The report

The written report is [`docs/report.pdf`](docs/report.pdf). It covers API security, the endpoints,
the benchmark results and what is wrong with Basic Auth. If you rerun the benchmark and want the
report to match, rebuild it with:

```bash
python3 docs/build_report.py
```

---

## A note on security

Basic Auth only base64-encodes the username and password, and base64 can be undone by anyone in one
command. It is encoding, not encryption. We used it because the assignment asked for it, but it is
not something you would put in front of real mobile money data.
[`docs/security_notes.md`](docs/security_notes.md) explains the problems and covers JWT and OAuth 2.0
as better options.
