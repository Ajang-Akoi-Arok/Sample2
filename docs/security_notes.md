# Security Notes — Basic Authentication and Stronger Alternatives

This API protects every endpoint with **HTTP Basic Authentication**. This document explains how it
works here, why Basic Auth is considered weak, and which stronger schemes should replace it in a
production deployment.

---

## 1. How Basic Auth works in this API

On every request the client sends an `Authorization` header:

```
Authorization: Basic YWRtaW46bW9tbzIwMjU=
```

The value after `Basic ` is `base64(username:password)`. In [`api/app.py`](../api/app.py) the
`authenticated()` method:

1. Rejects the request with **401** if the header is missing or does not start with `Basic `.
2. Base64-decodes the credentials, rejecting malformed input with **401**.
3. Compares the username and password using `hmac.compare_digest()`.
4. Returns **401** with a `WWW-Authenticate: Basic realm="MoMo Transactions API"` header when the
   credentials do not match.

`hmac.compare_digest()` is used instead of `==` because a normal string comparison returns as soon
as it finds the first differing character. An attacker could measure those tiny timing differences
to guess the password one character at a time. `compare_digest()` always takes the same amount of
time, which removes that side channel.

Credentials are read from the environment (`API_USERNAME` / `API_PASSWORD`) so they are not
compiled into the source code, with development defaults of `admin` / `momo2025`.

---

## 2. Why Basic Auth is weak

### 2.1 Base64 is encoding, not encryption

This is the core problem. Base64 is a reversible transformation with no key and no secret — anyone
can decode it instantly:

```bash
$ echo -n 'admin:momo2025' | base64
YWRtaW46bW9tbzIwMjU=

$ echo 'YWRtaW46bW9tbzIwMjU=' | base64 --decode
admin:momo2025
```

The credentials are effectively sent in plain text. Over plain HTTP, anyone able to observe the
traffic — someone on the same public Wi-Fi, a compromised router, an ISP — reads the real password
straight off the wire. Basic Auth is only ever acceptable over HTTPS, and even then the weaknesses
below remain.

### 2.2 The password is replayed on every single request

HTTP is stateless, so the client must resend the password with *every* request. One leaked request
— in a proxy log, a browser history entry, a crash report, a screenshot — exposes the password
permanently. A token-based scheme sends the real secret once, at login, and everything afterwards
uses a short-lived token.

### 2.3 No expiry and no way to revoke

A Basic Auth credential is valid until someone manually changes the password. There is no built-in
expiry. If a password leaks, the only remedy is to change it — which immediately breaks every other
client using that same account. Tokens, by contrast, expire on their own and can be revoked
individually.

### 2.4 No identity and no granularity

This API has a single shared `admin` account. That creates three problems:

- **No accountability.** The server logs show that "admin" deleted transaction 412, but not *who*.
  With shared credentials there is no audit trail.
- **No least privilege.** Every authenticated caller gets full CRUD. A mobile app that only needs
  `GET /transactions` holds a credential that can also `DELETE` records.
- **No per-client revocation.** Rotating the password to cut off one client cuts off all of them.

### 2.5 Vulnerable to brute force

The credential is a single static password with no lockout, rate limiting, or second factor in this
implementation. An attacker can try passwords as fast as the server will answer.

### 2.6 Summary

| Weakness | Consequence |
|---|---|
| Base64 is not encryption | Password readable by anyone observing traffic |
| Password resent on every request | Many chances to leak; one leak is permanent |
| No expiry | A stolen credential works forever |
| No revocation | Cannot cut off one client without breaking all |
| Single shared account | No audit trail, no least privilege |
| No rate limiting | Open to brute-force guessing |

---

## 3. Stronger alternatives

### 3.1 JWT (JSON Web Tokens)

The client authenticates **once** at a `/login` endpoint and receives a signed token. Every later
request sends that token instead of the password:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJyb2xlIjoicmVhZGVyIn0.<signature>
```

A JWT has three parts — header, payload, signature. The payload carries claims such as the user id,
their role, and an `exp` (expiry) timestamp. The signature is produced with a secret key held only
by the server, so the server can verify the token has not been tampered with without storing any
session state.

**What this fixes:**

- The real password crosses the network once, not on every request.
- Tokens expire automatically (`exp`), so a stolen token is useful only briefly.
- Claims carry identity and role, enabling per-user audit logs and least privilege — a read-only
  token can be issued to a client that only needs `GET`.
- Short-lived access tokens paired with longer-lived refresh tokens allow revocation at refresh
  time.

**Trade-offs:** a JWT is signed, not encrypted, so its payload is still readable — never put
secrets in it. Because verification is stateless, an issued token cannot easily be invalidated
before it expires, which is why access tokens are kept short-lived (minutes) and backed by a
refresh-token flow.

### 3.2 OAuth 2.0

OAuth 2.0 is an authorization *framework* rather than a single mechanism, and it is the right choice
when third parties are involved. Instead of a client ever holding the user's password, an
authorization server issues scoped access tokens.

For a MoMo system this matters directly: a budgeting app could be granted a token with scope
`transactions:read` and nothing more. It could list transactions but never delete one, and the user
could revoke that app's access at any time without changing their own password or affecting any
other app.

**What this fixes:**

- Third-party apps never see the user's credentials.
- **Scopes** enforce least privilege (`transactions:read` vs `transactions:write`).
- Access can be revoked per application.
- The token lifecycle — issue, refresh, revoke — is handled by a dedicated authorization server.

**Trade-offs:** considerably more complex to implement and operate, and it needs an authorization
server. That complexity is justified for multi-client or third-party access, and is overkill for a
single trusted internal client.

### 3.3 Supporting measures

Whichever scheme is used, these apply regardless:

- **HTTPS/TLS everywhere** — mandatory. It encrypts the whole exchange, including headers. Without
  it, every scheme above leaks its credential or token in transit.
- **Hashed password storage** — store passwords with a slow, salted hash such as bcrypt or Argon2,
  never in plain text.
- **Rate limiting and lockout** on the login endpoint to blunt brute-force attempts.
- **Per-user accounts with roles** instead of one shared `admin`, so actions are attributable.
- **Server-side audit logging** of every write operation, recording who changed what and when.

---

## 4. Conclusion

Basic Authentication is implemented correctly here — constant-time comparison, credentials taken
from the environment, correct `401` responses with a `WWW-Authenticate` challenge, and handling for
missing and malformed headers. It is a reasonable fit for a coursework project with a single trusted
client.

It is not suitable for real mobile money data. Because Base64 is encoding rather than encryption,
the password is effectively transmitted in the clear and is resent on every request, with no expiry,
no revocation, and no per-user identity. A production version of this API should run over HTTPS and
issue short-lived JWTs for first-party clients, adding OAuth 2.0 scopes once third-party
applications need access to the data.
