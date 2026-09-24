# Security Notes — What Is Wrong With Basic Auth, and What To Use Instead

This API uses HTTP Basic Authentication on every endpoint, because that is what the assignment asked
for. This file explains how we implemented it, why Basic Auth is a weak choice on its own, and what
a real system would use in its place.

---

## 1. How our login works

With every request, the client sends a header like this:

```
Authorization: Basic YWRtaW46bW9tbzIwMjU=
```

The part after `Basic ` is just the username and password stuck together with a colon and then
base64-encoded. In [`api/app.py`](../api/app.py), the `authenticated()` method does four things:

1. If there is no header, or it does not start with `Basic `, it sends back a **401** and stops.
2. It decodes the base64. If that fails because the header is malformed, it sends back a **401**.
3. It compares the username and password using `hmac.compare_digest()`.
4. If either one does not match, it sends back a **401** with a
   `WWW-Authenticate: Basic realm="MoMo Transactions API"` header.

The reason we used `hmac.compare_digest()` instead of a normal `==` is worth explaining. When Python
compares two strings with `==`, it stops as soon as it hits a character that does not match. So
comparing `"aaaa"` to `"bbbb"` finishes faster than comparing `"aaaa"` to `"aaab"`. That difference
is tiny, but an attacker who can measure it carefully can use it to work out the password one
character at a time. `compare_digest()` always takes the same amount of time no matter where the
difference is, so there is nothing to measure.

We also kept the credentials out of the code. They come from the `API_USERNAME` and `API_PASSWORD`
environment variables, and only fall back to `admin` / `momo2025` for development. That way the real
password never has to be committed to git.

---

## 2. Why Basic Auth is weak

### 2.1 Base64 is not encryption

This is the main problem, and it is worth being clear about it. Base64 is not a security measure at
all. There is no key and no secret involved, so anybody can undo it:

```bash
$ echo -n 'admin:momo2025' | base64
YWRtaW46bW9tbzIwMjU=

$ echo 'YWRtaW46bW9tbzIwMjU=' | base64 --decode
admin:momo2025
```

So when we say the credentials are "encoded", that is all it is. The password is effectively being
sent in plain text. If the connection is plain HTTP, then anyone who can see the traffic can read
the real password straight off the wire. That could be someone else on the same coffee shop wifi, a
router that has been tampered with, or the internet provider. Basic Auth is only acceptable at all
if everything is running over HTTPS, and even then the problems below do not go away.

### 2.2 The password is sent over and over

HTTP does not remember anything between requests, so the client has to send the password again every
single time it asks for something. Load a page that makes thirty API calls and the password has gone
over the network thirty times.

Each one of those is a chance for it to be captured or to get written down somewhere it should not
be, like a proxy log or an error report. And because it is the real password and not a temporary
stand-in, one leak is permanent.

### 2.3 It does not expire and you cannot cancel it

A Basic Auth password stays valid until a human changes it. There is no built-in expiry date. So if
it does leak, you will not find out, and it will keep working until somebody notices.

Changing the password is the only way to shut it down, and that is a blunt instrument. If five
different apps are using the same login, changing it breaks all five at once, including the four
that were never compromised.

### 2.4 One account for everybody

Our API has a single `admin` login that everyone shares. That causes three separate problems:

First, there is no way to tell who did what. If a record gets deleted, the server log says "admin"
deleted it. It does not say which person, because as far as the server is concerned there is only
one user.

Second, everyone gets full access whether they need it or not. A mobile app that only ever reads
transactions still has to hold a password that can delete every record in the database.

Third, you cannot cut off one client. Rotating the password to lock out an app you no longer trust
locks out everybody else too.

### 2.5 Nothing stops someone guessing

Our implementation has no rate limiting, no account lockout after failed attempts, and no second
factor. An attacker can just keep trying passwords as fast as the server will answer them.

### 2.6 Summary

| The problem | What it means in practice |
|---|---|
| Base64 is not encryption | Anyone watching the traffic reads the password |
| Sent on every request | Many chances to leak, and one leak is permanent |
| Never expires | A stolen password works forever |
| Cannot be revoked | Cutting off one client breaks all of them |
| One shared account | No record of who did what, and no limited access |
| No rate limiting | Passwords can be guessed at full speed |

---

## 3. Better options

### 3.1 JWT (JSON Web Tokens)

With JWT, the client sends its username and password once, to a login endpoint, and gets back a
token. After that it sends the token instead of the password:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJyb2xlIjoicmVhZGVyIn0.<signature>
```

A token has three parts. The middle part holds claims, which is just information about the user:
who they are, what role they have, and an expiry time. The third part is a signature made with a
secret key that only the server knows, so the server can check the token has not been altered
without having to store anything about the session.

This fixes most of what is wrong above. The actual password crosses the network once instead of
hundreds of times. Tokens expire on their own, so a stolen one is only useful for a few minutes.
And because the token says who the user is and what they are allowed to do, you can keep a proper
audit log and give a read-only app a read-only token.

It is not perfect. A JWT is signed but not encrypted, which means anyone holding it can read what is
inside, so you must never put anything secret in there. And since the server checks the signature
rather than looking the token up in a database, you cannot easily cancel a token before it expires.
The usual answer is to make access tokens short-lived and hand out a longer-lived refresh token
alongside them, which gives you a point where access can be denied.

### 3.2 OAuth 2.0

OAuth 2.0 is bigger than a single login mechanism. It is a whole framework, and it is the right
choice once other people's applications are involved. Rather than the client holding the user's
password, a separate authorization server issues access tokens with scopes attached.

The scopes are the useful part. Imagine a budgeting app that wants to show someone their MoMo
spending. With OAuth 2.0 it can be given a token with the scope `transactions:read` and nothing
more. It can list transactions, and that is it, and the user can revoke that one app whenever they
want without changing their password or affecting any other app they use.

The trade-off is that OAuth 2.0 is a lot more work to set up and needs an authorization server
running. For a project with one trusted client it is overkill. For anything where third parties need
access, it is the standard for good reason.

### 3.3 Things you should do either way

None of the above helps much on its own. These go with it:

- **Use HTTPS.** This one is not optional. TLS encrypts the whole request including the headers.
  Without it, every scheme here leaks its password or token in transit.
- **Hash stored passwords** with something slow and salted like bcrypt or Argon2. Never store them
  as plain text.
- **Rate limit the login endpoint** and lock accounts after repeated failures, so guessing does not
  scale.
- **Give each person their own account** with a role, instead of one shared `admin`, so you can tell
  who did what.
- **Log every write** with the user, the action and the time.

---

## 4. Conclusion

We think the Basic Auth in this project is implemented properly. The credentials come from the
environment rather than the source code, the comparison is constant-time, the 401 responses include
the right challenge header, and missing or malformed headers are handled instead of crashing the
server.

The scheme itself is still the weakest part of the project, and it would not be acceptable for real
mobile money data. Base64 is encoding and not encryption, so the password is effectively in the
clear, it is resent constantly, it never expires, it cannot be revoked, and there is no way to tell
one user from another.

If this were going to be used for real, we would put it behind HTTPS and switch to short-lived JWTs
for our own apps, then add OAuth 2.0 scopes later if other people's applications ever needed access
to the data.
