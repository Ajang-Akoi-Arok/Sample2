# MoMo SMS Transactions API — Documentation

This API serves 1,691 MTN Mobile Money SMS records that were parsed out of
`data/modified_sms_v2.xml`.

- **Base URL:** `http://localhost:8000`
- **Format:** JSON, both for what you send and what you get back
- **Authentication:** HTTP Basic, required on every endpoint

---

## Logging in

Every request needs an `Authorization` header holding your username and password, base64-encoded.

| Setting | Default | Environment variable |
|---|---|---|
| Username | `admin` | `API_USERNAME` |
| Password | `momo2025` | `API_PASSWORD` |

You do not have to build the header yourself. curl does it for you with `-u`:

```bash
# curl builds the header
curl -u admin:momo2025 http://localhost:8000/transactions

# the same thing, written out
curl -H "Authorization: Basic YWRtaW46bW9tbzIwMjU=" http://localhost:8000/transactions
```

If the header is missing, broken, or the password is wrong, you get a **401 Unauthorized** back
along with a `WWW-Authenticate` header:

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

## What a transaction looks like

| Field | Type | What it is |
|---|---|---|
| `id` | integer | The record's id. The server sets this, you do not |
| `transaction_type` | string | What kind of transaction it is, like `incoming_money` or `bank_deposit` |
| `amount` | number or null | How much, in RWF |
| `fee` | number or null | The fee charged, in RWF |
| `new_balance` | number or null | The balance after the transaction |
| `sender` / `sender_phone` | string or null | Who sent the money |
| `receiver` / `receiver_phone` | string or null | Who received it |
| `receiver_code` | string or null | The merchant or code-holder number |
| `account` | string or null | The mobile money account used |
| `financial_transaction_id` | string or null | MTN's own reference for the transaction |
| `timestamp` | string or null | When it happened, in ISO-8601 |
| `readable_date` | string or null | The date as it appeared in the SMS export |
| `service_center` | string or null | The SMS service centre number |
| `address` | string or null | Who the SMS came from, usually `M-Money` |
| `body` | string or null | The original text of the SMS |

A lot of these are null on any given record, and that is expected. An outgoing payment has a
receiver but no named sender, because the sender is the account holder. An OTP message has neither.
The parser only fills in what the SMS actually says.

**What is in the dataset**

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

Every record in the file falls into one of these. Nothing was left unrecognised.

---

## The endpoints

### 1. `GET /transactions` — get everything

Returns all the transactions currently in the store.

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

**Error codes**

| Code | What it means |
|---|---|
| `200` | It worked |
| `401` | Your credentials were missing or wrong |

---

### 2. `GET /transactions/{id}` — get one record

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

**Response — `404 Not Found`** if there is no record with that id:
```json
{
  "error": "Transaction 99999 not found",
  "status": 404
}
```

**Error codes**

| Code | What it means |
|---|---|
| `200` | Found it |
| `401` | Your credentials were missing or wrong |
| `404` | No record has that id |

---

### 3. `POST /transactions` — add a record

You have to send `transaction_type` and `amount`. Everything else is optional and comes back as
null if you leave it out. The server picks the id, so do not send one.

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

**Response — `400 Bad Request`** if something is wrong with what you sent:
```json
{
  "error": "Missing required field(s): transaction_type",
  "status": 400
}
```

**Error codes**

| Code | What it means |
|---|---|
| `201` | The record was created |
| `400` | The body was not valid JSON, a required field was missing, you sent a field we do not recognise, or `amount` / `fee` / `new_balance` was negative or not a number |
| `401` | Your credentials were missing or wrong |

---

### 4. `PUT /transactions/{id}` — change a record

Send only the fields you want to change. Anything you leave out stays as it was. You cannot change
the id.

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

**Error codes**

| Code | What it means |
|---|---|
| `200` | The record was updated |
| `400` | Bad JSON, an unknown field, or an invalid number |
| `401` | Your credentials were missing or wrong |
| `404` | No record has that id |

---

### 5. `DELETE /transactions/{id}` — remove a record

**Request**
```bash
curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692
```

**Response — `200 OK`**. The record you deleted comes back with the confirmation, so you can see
what was removed:
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

**Error codes**

| Code | What it means |
|---|---|
| `200` | The record was deleted |
| `401` | Your credentials were missing or wrong |
| `404` | No record has that id |

---

## All the error codes in one place

| Code | Name | When you get it |
|---|---|---|
| `200` | OK | A GET, PUT or DELETE worked |
| `201` | Created | A POST worked |
| `400` | Bad Request | Broken JSON, a missing required field, a field we do not recognise, or a bad number |
| `401` | Unauthorized | No credentials, broken credentials, or the wrong password |
| `404` | Not Found | That id does not exist, or that URL is not one of our endpoints |

Errors always come back in the same shape, so you can handle them the same way every time:

```json
{ "error": "<what went wrong>", "status": <code> }
```

---

## Security notes

Basic Auth protects all of the endpoints above, but it has real problems, and they matter more than
usual when the data is people's money. The short version:

- **Base64 is not encryption.** `YWRtaW46bW9tbzIwMjU=` turns back into `admin:momo2025` with one
  command that anybody can run, so the password is basically travelling in plain text. Basic Auth is
  only safe if the whole connection is running over HTTPS.
- **The password gets sent again on every single request.** The more times it goes over the wire,
  the more chances it has to end up in a log file, a crash report or someone's screenshot.
- **It never expires and you cannot revoke it.** The only way to cancel a credential is to change
  the password, and that breaks every other client at the same time.
- **Everyone shares one account.** The log tells you "admin" deleted a record but not which person
  that was, and a read-only mobile app ends up holding a password that can also delete things.
- **Nothing stops guessing.** There is no rate limit and no lockout, so an attacker can try
  passwords as fast as the server can answer.

Better options are **JWT**, where you log in once and get back a signed token that expires on its
own and says who you are and what you are allowed to do, and **OAuth 2.0**, where an authorization
server hands out scoped tokens so a third-party app can be given read access only and can be cut off
without changing anyone's password. Either way the connection should be HTTPS and passwords should
be stored hashed.

There is a longer write-up in [`security_notes.md`](security_notes.md).

---

## Testing

The full transcript of the curl tests is saved in
[`../screenshots/api_test_results.txt`](../screenshots/api_test_results.txt). To regenerate it, start
the server in one terminal:

```bash
python3 api/app.py
```

and run the tests in another:

```bash
bash screenshots/run_tests.sh
```
