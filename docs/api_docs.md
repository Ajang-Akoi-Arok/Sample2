# MoMo SMS Transactions API — Documentation

REST API over 1,691 MTN Mobile Money SMS records parsed from `data/modified_sms_v2.xml`.

- **Base URL:** `http://localhost:8000`
- **Format:** JSON (request and response)
- **Authentication:** HTTP Basic — **required on every endpoint**

---

## Authentication

Every request must carry an `Authorization: Basic <base64(username:password)>` header.

| Setting | Default | Environment variable |
|---|---|---|
| Username | `admin` | `API_USERNAME` |
| Password | `momo2025` | `API_PASSWORD` |

```bash
# curl builds the header for you
curl -u admin:momo2025 http://localhost:8000/transactions

# equivalent explicit header
curl -H "Authorization: Basic YWRtaW46bW9tbzIwMjU=" http://localhost:8000/transactions
```

A missing, malformed or incorrect credential returns **401 Unauthorized** together with a
`WWW-Authenticate: Basic realm="MoMo Transactions API"` header.

```http
HTTP/1.0 401 Unauthorized
WWW-Authenticate: Basic realm="MoMo Transactions API"
Content-Type: application/json

{
  "error": "Unauthorized: invalid username or password",
  "status": 401
}
```

---

## Transaction object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Unique identifier, assigned by the server |
| `transaction_type` | string | Category, e.g. `incoming_money`, `transfer_to_mobile`, `bank_deposit` |
| `amount` | number \| null | Transaction amount in RWF |
| `fee` | number \| null | Fee charged in RWF |
| `new_balance` | number \| null | Account balance after the transaction |
| `sender` / `sender_phone` | string \| null | Originating party |
| `receiver` / `receiver_phone` | string \| null | Receiving party |
| `receiver_code` | string \| null | Merchant/code-holder number |
| `account` | string \| null | Mobile money account used |
| `financial_transaction_id` | string \| null | MTN transaction reference |
| `timestamp` | string \| null | ISO-8601 time of the transaction |
| `readable_date` | string \| null | Human-readable date from the SMS export |
| `service_center` | string \| null | SMS service centre number from the export |
| `address` | string \| null | SMS sender address (e.g. `M-Money`) |
| `body` | string \| null | Original SMS text |

**Transaction types present in the dataset**

| Type | Count |
|---|---|
| `payment_to_code_holder` | 658 |
| `transfer_to_mobile` | 585 |
| `bank_deposit` | 249 |
| `incoming_money` | 63 |
| `bill_or_airtime_payment` | 53 |
| `third_party_payment` | 36 |
| `bundle_purchase_notice` | 21 |
| `otp` | 8 |
| `bank_transfer` | 6 |
| `failed_transaction` | 5 |
| `withdrawal` | 3 |
| `reversal` / `merchant_payment` | 2 each |

Every record in the dataset matches one of the categories above; there are no unclassified records.

---

## Endpoints

### 1. `GET /transactions` — list all transactions

Returns every transaction in the store.

**Request**
```bash
curl -u admin:momo2025 http://localhost:8000/transactions
```

**Response — `200 OK`**
```json
{
  "count": 1691,
  "transactions": [
    {
      "id": 1,
      "transaction_type": "incoming_money",
      "amount": 2000.0,
      "fee": null,
      "new_balance": 2000.0,
      "sender": "Jane Smith",
      "sender_phone": "*********013",
      "receiver": null,
      "financial_transaction_id": "76662021700",
      "timestamp": "2024-05-10T16:30:51",
      "readable_date": "10 May 2024 4:30:58 PM",
      "body": "You have received 2000 RWF from Jane Smith (*********013) ..."
    }
  ]
}
```

| Code | Meaning |
|---|---|
| `200` | Success |
| `401` | Missing or invalid credentials |

---

### 2. `GET /transactions/{id}` — retrieve one transaction

**Request**
```bash
curl -u admin:momo2025 http://localhost:8000/transactions/1
```

**Response — `200 OK`**
```json
{
  "id": 1,
  "transaction_type": "incoming_money",
  "amount": 2000.0,
  "new_balance": 2000.0,
  "sender": "Jane Smith",
  "sender_phone": "*********013",
  "financial_transaction_id": "76662021700",
  "timestamp": "2024-05-10T16:30:51"
}
```

**Response — `404 Not Found`**
```json
{
  "error": "Transaction 99999 not found",
  "status": 404
}
```

| Code | Meaning |
|---|---|
| `200` | Transaction found |
| `401` | Missing or invalid credentials |
| `404` | No transaction with that id |

---

### 3. `POST /transactions` — create a transaction

Required fields: `transaction_type`, `amount`. All other fields are optional and default to `null`.
The server assigns the `id`.

**Request**
```bash
curl -u admin:momo2025 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
        "transaction_type": "incoming_money",
        "amount": 7500,
        "fee": 0,
        "sender": "Chol Deng",
        "receiver": "Test Account",
        "timestamp": "2025-09-19T10:00:00"
      }'
```

**Response — `201 Created`**
```json
{
  "id": 1692,
  "transaction_type": "incoming_money",
  "amount": 7500.0,
  "fee": 0.0,
  "new_balance": null,
  "sender": "Chol Deng",
  "receiver": "Test Account",
  "timestamp": "2025-09-19T10:00:00",
  "body": null
}
```

**Response — `400 Bad Request`**
```json
{
  "error": "Missing required field(s): transaction_type",
  "status": 400
}
```

| Code | Meaning |
|---|---|
| `201` | Transaction created |
| `400` | Body is not JSON, required field missing, unknown field, or `amount`/`fee`/`new_balance` is non-numeric or negative |
| `401` | Missing or invalid credentials |

---

### 4. `PUT /transactions/{id}` — update a transaction

Partial updates are accepted: send only the fields you want to change. `id` cannot be changed.

**Request**
```bash
curl -u admin:momo2025 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" \
  -d '{"amount": 9900, "receiver": "Updated Account"}'
```

**Response — `200 OK`**
```json
{
  "id": 1692,
  "transaction_type": "incoming_money",
  "amount": 9900.0,
  "fee": 0.0,
  "sender": "Chol Deng",
  "receiver": "Updated Account",
  "timestamp": "2025-09-19T10:00:00"
}
```

| Code | Meaning |
|---|---|
| `200` | Transaction updated |
| `400` | Invalid JSON, unknown field, or invalid numeric value |
| `401` | Missing or invalid credentials |
| `404` | No transaction with that id |

---

### 5. `DELETE /transactions/{id}` — delete a transaction

**Request**
```bash
curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692
```

**Response — `200 OK`**
```json
{
  "message": "Transaction 1692 deleted",
  "deleted": {
    "id": 1692,
    "transaction_type": "incoming_money",
    "amount": 9900.0,
    "receiver": "Updated Account"
  }
}
```

| Code | Meaning |
|---|---|
| `200` | Transaction deleted |
| `401` | Missing or invalid credentials |
| `404` | No transaction with that id |

---

## Error code summary

| Code | Name | When it occurs |
|---|---|---|
| `200` | OK | Successful GET, PUT or DELETE |
| `201` | Created | Successful POST |
| `400` | Bad Request | Malformed JSON, missing required field, unknown field, invalid numeric value |
| `401` | Unauthorized | Absent, malformed or incorrect Basic Auth credentials |
| `404` | Not Found | Unknown transaction id or unknown endpoint |

All errors share the same shape:

```json
{ "error": "<human-readable message>", "status": <code> }
```

---

## Security notes

Basic Authentication protects every endpoint above, but the scheme has real limits that matter for
financial data. In short:

- **Base64 is encoding, not encryption.** `YWRtaW46bW9tbzIwMjU=` decodes to `admin:momo2025` with a
  single shell command, so the password is effectively sent in clear text. Basic Auth is only ever
  acceptable over HTTPS.
- **The password is replayed on every request**, multiplying the chances of it leaking into a log,
  a crash report or a screenshot.
- **No expiry and no revocation.** The credential is valid until someone changes the password, and
  changing it breaks every other client at once.
- **One shared account** means no audit trail (the log shows "admin", not *who*) and no least
  privilege, since a read-only client holds a credential that can also `DELETE`.
- **No rate limiting**, so an attacker can brute-force at the speed the server responds.

Stronger alternatives are **JWT** (a signed, expiring token issued once at login, carrying user and
role claims) and **OAuth 2.0** (scoped tokens issued to third-party apps, revocable per app, so the
app never sees the user's password). Both should run over HTTPS with hashed password storage.

Full discussion: [`security_notes.md`](security_notes.md).

---

## Testing

The full request/response transcript lives in [`../screenshots/api_test_results.txt`](../screenshots/api_test_results.txt)
and can be regenerated with:

```bash
python3 api/app.py &          # terminal 1
bash screenshots/run_tests.sh # terminal 2
```
