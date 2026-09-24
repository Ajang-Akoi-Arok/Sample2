"""Generate docs/report.pdf — the written report for the REST API assignment.

The DSA table is read straight out of screenshots/dsa_results.txt so the report can
never drift from the benchmark that was actually run.

Usage:  python3 docs/build_report.py
"""

import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ---------------------------------------------------------------- edit me ----
TEAM_NAME = "Team dema3"
AUTHORS = "Chol Deng"
COURSE = "Building and Securing a REST API"
REPO_URL = "https://github.com/Chol1000/dema3"
# -----------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DSA_RESULTS = os.path.join(BASE_DIR, "screenshots", "dsa_results.txt")
OUT_PDF = os.path.join(BASE_DIR, "docs", "report.pdf")

INK = colors.HexColor("#1a1a1a")
ACCENT = colors.HexColor("#0b5394")
RULE = colors.HexColor("#c8d2dc")
BAND = colors.HexColor("#eef3f8")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=styles["Title"], fontSize=20, leading=25,
                            textColor=ACCENT, spaceAfter=2),
    "sub": ParagraphStyle("sub", parent=styles["Normal"], fontSize=10.5, leading=15,
                          textColor=colors.HexColor("#555555"), alignment=1),
    "h1": ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, leading=18,
                         textColor=ACCENT, spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11.5, leading=15,
                         textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14.5,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=7),
    "bullet": ParagraphStyle("bullet", parent=styles["Normal"], fontSize=10, leading=14.5,
                             textColor=INK, leftIndent=14, bulletIndent=4, spaceAfter=4),
    "code": ParagraphStyle("code", parent=styles["Normal"], fontName="Courier",
                           fontSize=8.5, leading=11.5, textColor=INK,
                           backColor=BAND, borderPadding=6, leftIndent=2, spaceAfter=8),
    "caption": ParagraphStyle("caption", parent=styles["Normal"], fontSize=8.5, leading=11,
                              textColor=colors.HexColor("#666666"), spaceAfter=10),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="\u2022") for t in items]


def rule():
    return HRFlowable(width="100%", thickness=0.7, color=RULE,
                      spaceBefore=3, spaceAfter=9)


def grid(data, widths, align_right=()):
    """A simple striped table with a header row."""
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]),
    ]
    for col in align_right:
        cmds.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(cmds))
    return t


def read_dsa_results():
    """Pull the measured rows and the average line out of dsa_results.txt."""
    rows, average = [], None
    with open(DSA_RESULTS, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(
                r"\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)x\s+(\d+)\s+(\d+)\s*$", line)
            if m:
                rows.append(m.groups())
                continue
            m = re.match(
                r"\s*AVERAGE\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)x\s+([\d.]+)\s+([\d.]+)", line)
            if m:
                average = m.groups()
    if not rows or average is None:
        raise SystemExit("Could not read dsa_results.txt — run dsa/dsa_comparison.py first.")
    return rows, average


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(2.2 * cm, 1.25 * cm, f"{COURSE} — {TEAM_NAME}")
    canvas.drawRightString(A4[0] - 2.2 * cm, 1.25 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(2.2 * cm, 1.6 * cm, A4[0] - 2.2 * cm, 1.6 * cm)
    canvas.restoreState()


def build():
    rows, average = read_dsa_results()
    lin_avg, dict_avg, speedup, lin_cmps_avg, dict_cmps_avg = average

    doc = SimpleDocTemplate(
        OUT_PDF, pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.0 * cm, bottomMargin=2.2 * cm,
        title="Building and Securing a REST API — MoMo SMS Transactions",
        author=AUTHORS,
    )
    s = []

    # ------------------------------------------------------------- header --
    s.append(P("Building and Securing a REST API", "title"))
    s.append(P("MoMo SMS Transactions API", "sub"))
    s.append(Spacer(1, 6))
    s.append(P(f"{TEAM_NAME} &nbsp;|&nbsp; {AUTHORS}<br/>"
               f'Repository: <font color="#0b5394">{REPO_URL}</font>', "sub"))
    s.append(Spacer(1, 10))
    s.append(rule())

    # ------------------------------------------------------- 1. intro sec --
    s.append(P("1. Introduction to API Security", "h1"))
    s.append(P(
        "An API is the door through which every client application reaches the data behind it. "
        "For a mobile money system that data is highly sensitive: transaction amounts, account "
        "balances, phone numbers and the names of both parties to a payment. If that door is left "
        "unlocked, anyone who can reach the server can read every customer's financial history, or "
        "worse, modify and delete records. API security is therefore not an optional extra bolted "
        "on at the end; it is a basic requirement of the design."))
    s.append(P(
        "Securing an API rests on three distinct ideas that are easily confused. "
        "<b>Authentication</b> answers \"who is making this request?\". "
        "<b>Authorization</b> answers \"is this caller allowed to do this particular thing?\". "
        "<b>Confidentiality</b> answers \"can anyone else read this exchange while it travels across "
        "the network?\", and is provided by transport encryption (HTTPS/TLS). A system needs all "
        "three. Strong authentication is worthless if the credential is transmitted in clear text, "
        "and encryption is worthless if every authenticated caller is allowed to delete anything."))
    s.append(P(
        "This project implements the first of those three using HTTP Basic Authentication, as "
        "required by the assignment. Every endpoint rejects unauthenticated requests with a "
        "<b>401 Unauthorized</b> response. Section 5 examines honestly where that scheme falls "
        "short and what a production deployment would use instead."))

    # -------------------------------------------------- 2. system overview --
    s.append(P("2. System Overview and Data Parsing", "h1"))
    s.append(P(
        "The source dataset, <font face='Courier'>modified_sms_v2.xml</font>, is an SMS backup "
        "export containing 1,691 <font face='Courier'>&lt;sms&gt;</font> elements from an MTN "
        "Mobile Money account. The useful content sits in the <font face='Courier'>body</font> "
        "attribute of each element as free-form human-readable text, so the parser has to read "
        "meaning out of prose rather than out of structured fields."))
    s.append(P(
        "<font face='Courier'>dsa/parse_xml.py</font> handles this with a list of labelled regular "
        "expressions. Each SMS body is tested against the patterns in order; the first match "
        "determines the transaction category and supplies the named capture groups for amount, fee, "
        "new balance, sender, receiver, account and transaction id. Amounts written as "
        "\"12,500\" are normalised to floats, and timestamps are converted to ISO-8601. Where a "
        "message carries no readable timestamp, the parser falls back to the epoch "
        "<font face='Courier'>date</font> attribute on the element."))
    s.append(P("The 1,691 records break down as follows:"))

    counts = [
        ("payment_to_code_holder", "658"), ("transfer_to_mobile", "585"),
        ("bank_deposit", "249"), ("incoming_money", "63"),
        ("bill_or_airtime_payment", "53"), ("third_party_payment", "36"),
        ("bundle_purchase_notice", "21"), ("otp", "8"),
        ("bank_transfer", "6"), ("failed_transaction", "5"),
        ("withdrawal", "3"), ("reversal", "2"), ("merchant_payment", "2"),
    ]
    half = (len(counts) + 1) // 2
    left, right = counts[:half], counts[half:]
    while len(right) < len(left):
        right.append(("", ""))
    data = [["Transaction type", "Count", "Transaction type", "Count"]]
    data += [[l[0], l[1], r[0], r[1]] for l, r in zip(left, right)]
    s.append(grid(data, [4.7 * cm, 1.7 * cm, 4.7 * cm, 1.7 * cm], align_right=(1, 3)))
    s.append(Spacer(1, 4))
    s.append(P("Table 1 — Records per transaction type. All 1,691 records are classified; "
               "none fall into an unrecognised category.", "caption"))
    s.append(P(
        "The parser writes the result to <font face='Courier'>data/transactions.json</font> as a "
        "list of dictionaries, which is exactly the shape the API then serves."))

    s.append(PageBreak())

    # ------------------------------------------------ 3. endpoint docs -----
    s.append(P("3. API Endpoint Documentation", "h1"))
    s.append(P(
        "The API is written in plain Python on top of "
        "<font face='Courier'>http.server</font>, with no third-party dependencies. It exposes five "
        "CRUD endpoints over the parsed transactions. Records are held in memory in a dictionary "
        "keyed by id, so lookups by id are O(1) (see Section 6). <b>Every endpoint requires Basic "
        "Authentication.</b>"))

    ep = [["Method", "Endpoint", "Purpose", "Success"]]
    ep += [
        ["GET", "/transactions", "List all transactions", "200"],
        ["GET", "/transactions/{id}", "Retrieve one transaction", "200"],
        ["POST", "/transactions", "Create a transaction", "201"],
        ["PUT", "/transactions/{id}", "Update an existing record", "200"],
        ["DELETE", "/transactions/{id}", "Delete a record", "200"],
    ]
    s.append(grid(ep, [1.8 * cm, 4.4 * cm, 6.0 * cm, 1.6 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 2 — CRUD endpoints.", "caption"))

    s.append(P("3.1 Request and response examples", "h2"))

    s.append(P("<b>GET /transactions/1</b> — retrieve a single record", "body"))
    s.append(P("$ curl -u admin:momo2025 http://localhost:8000/transactions/1", "code"))
    s.append(P("HTTP/1.0 200 OK<br/>"
               "Content-Type: application/json<br/><br/>"
               "{<br/>"
               "&nbsp;&nbsp;\"id\": 1,<br/>"
               "&nbsp;&nbsp;\"transaction_type\": \"incoming_money\",<br/>"
               "&nbsp;&nbsp;\"amount\": 2000.0,<br/>"
               "&nbsp;&nbsp;\"new_balance\": 2000.0,<br/>"
               "&nbsp;&nbsp;\"sender\": \"Jane Smith\",<br/>"
               "&nbsp;&nbsp;\"sender_phone\": \"*********013\",<br/>"
               "&nbsp;&nbsp;\"financial_transaction_id\": \"76662021700\",<br/>"
               "&nbsp;&nbsp;\"timestamp\": \"2024-05-10T16:30:51\"<br/>"
               "}", "code"))

    s.append(P("<b>POST /transactions</b> — create a record. "
               "<font face='Courier'>transaction_type</font> and "
               "<font face='Courier'>amount</font> are required; the server assigns the id.", "body"))
    s.append(P("$ curl -u admin:momo2025 -X POST http://localhost:8000/transactions \\<br/>"
               "&nbsp;&nbsp;-H \"Content-Type: application/json\" \\<br/>"
               "&nbsp;&nbsp;-d '{\"transaction_type\":\"incoming_money\",\"amount\":7500,"
               "\"sender\":\"Chol Deng\"}'", "code"))
    s.append(P("HTTP/1.0 201 Created<br/><br/>"
               "{<br/>"
               "&nbsp;&nbsp;\"id\": 1692,<br/>"
               "&nbsp;&nbsp;\"transaction_type\": \"incoming_money\",<br/>"
               "&nbsp;&nbsp;\"amount\": 7500.0,<br/>"
               "&nbsp;&nbsp;\"sender\": \"Chol Deng\"<br/>"
               "}", "code"))

    s.append(P("<b>PUT /transactions/1692</b> — partial update; send only changed fields.", "body"))
    s.append(P("$ curl -u admin:momo2025 -X PUT http://localhost:8000/transactions/1692 \\<br/>"
               "&nbsp;&nbsp;-H \"Content-Type: application/json\" -d '{\"amount\":9900}'"
               "<br/><br/>HTTP/1.0 200 OK", "code"))

    s.append(P("<b>DELETE /transactions/1692</b> — remove a record.", "body"))
    s.append(P("$ curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692"
               "<br/><br/>HTTP/1.0 200 OK<br/>"
               "{ \"message\": \"Transaction 1692 deleted\", \"deleted\": { ... } }", "code"))

    s.append(P("<b>Unauthorised request</b> — wrong password.", "body"))
    s.append(P("$ curl -i -u admin:wrongpassword http://localhost:8000/transactions<br/><br/>"
               "HTTP/1.0 401 Unauthorized<br/>"
               "WWW-Authenticate: Basic realm=\"MoMo Transactions API\"<br/><br/>"
               "{ \"error\": \"Unauthorized: invalid username or password\", \"status\": 401 }",
               "code"))

    s.append(P("3.2 Error codes", "h2"))
    errs = [["Code", "Name", "When it occurs"]]
    errs += [
        ["200", "OK", "Successful GET, PUT or DELETE"],
        ["201", "Created", "Successful POST"],
        ["400", "Bad Request", "Malformed JSON, missing required field, unknown field, "
                               "or a negative / non-numeric amount"],
        ["401", "Unauthorized", "Absent, malformed or incorrect Basic Auth credentials"],
        ["404", "Not Found", "Unknown transaction id, or unknown endpoint"],
    ]
    s.append(grid(errs, [1.5 * cm, 2.6 * cm, 9.7 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 3 — Error codes. Every error shares the shape "
               "<font face='Courier'>{\"error\": ..., \"status\": ...}</font>. "
               "Full documentation is in <font face='Courier'>docs/api_docs.md</font>.", "caption"))

    s.append(PageBreak())

    # ---------------------------------------------- 4. auth implementation --
    s.append(P("4. Authentication Implementation", "h1"))
    s.append(P(
        "Each request must carry an <font face='Courier'>Authorization</font> header holding the "
        "Base64 encoding of <font face='Courier'>username:password</font>. The handler decodes it "
        "and compares both halves against the configured credentials before any route logic runs, "
        "so no endpoint can be reached without passing the check."))
    s.append(P("Authorization: Basic YWRtaW46bW9tbzIwMjU=", "code"))
    s.append(P("Three implementation details are worth highlighting:", "body"))
    s.extend(bullets([
        "<b>Constant-time comparison.</b> The credentials are checked with "
        "<font face='Courier'>hmac.compare_digest()</font> rather than <font face='Courier'>==</font>. "
        "A normal string comparison stops at the first differing character, and an attacker able to "
        "measure that timing difference could recover the password one character at a time. "
        "<font face='Courier'>compare_digest()</font> always takes the same time, closing that side channel.",
        "<b>Credentials are not hardcoded.</b> They are read from the "
        "<font face='Courier'>API_USERNAME</font> and <font face='Courier'>API_PASSWORD</font> "
        "environment variables, with development defaults, so the deployed secret never needs to "
        "live in source control.",
        "<b>Every failure mode returns 401.</b> A missing header, a header that is not "
        "<font face='Courier'>Basic</font>, corrupt Base64, and a simply wrong password are all "
        "handled and all answered with 401 plus a "
        "<font face='Courier'>WWW-Authenticate</font> challenge — never a 500.",
    ]))

    # ------------------------------------------------- 5. reflection -------
    s.append(P("5. Reflection: Why Basic Auth Is Weak", "h1"))
    s.append(P(
        "Basic Authentication is implemented correctly here, but the scheme itself is weak, and for "
        "real mobile money data it would not be acceptable."))

    s.append(P("5.1 Base64 is encoding, not encryption", "h2"))
    s.append(P(
        "This is the central flaw. Base64 uses no key and no secret, so the transformation is "
        "trivially reversible by anybody:"))
    s.append(P("$ echo -n 'admin:momo2025' | base64<br/>"
               "YWRtaW46bW9tbzIwMjU=<br/><br/>"
               "$ echo 'YWRtaW46bW9tbzIwMjU=' | base64 --decode<br/>"
               "admin:momo2025", "code"))
    s.append(P(
        "The password is therefore effectively sent in plain text. Over plain HTTP anyone able to "
        "observe the traffic — someone sharing a public Wi-Fi network, a compromised router, an ISP "
        "— reads the real password directly off the wire. Basic Auth is only ever tolerable over "
        "HTTPS, and even then the problems below remain."))

    s.append(P("5.2 Further limitations", "h2"))
    s.extend(bullets([
        "<b>The password is replayed on every request.</b> Because HTTP is stateless, the credential "
        "is resent with each call, multiplying the chances of it leaking into a proxy log, a crash "
        "report or a screenshot. One leak exposes it permanently.",
        "<b>No expiry and no revocation.</b> The credential stays valid until someone manually "
        "changes the password, and changing it breaks every other client using that same account.",
        "<b>A single shared account.</b> With one <font face='Courier'>admin</font> credential there "
        "is no audit trail — the log shows that \"admin\" deleted a record, not who — and no least "
        "privilege, since a read-only mobile client holds a credential that can also DELETE.",
        "<b>No brute-force protection.</b> The implementation has no rate limiting, lockout or "
        "second factor, so an attacker can guess passwords as fast as the server responds.",
    ]))

    s.append(P("5.3 Stronger alternatives", "h2"))
    s.append(P(
        "<b>JWT (JSON Web Tokens).</b> The client authenticates once at a login endpoint and "
        "receives a signed token, sent afterwards as "
        "<font face='Courier'>Authorization: Bearer &lt;token&gt;</font>. The token carries claims "
        "such as user id, role and an expiry timestamp, and is signed with a server-held key. This "
        "means the real password crosses the network only once, tokens expire on their own so a "
        "stolen one is useful only briefly, and the embedded claims enable per-user audit logs and "
        "role-based access. The trade-off is that a JWT is signed but not encrypted, so its payload "
        "is still readable and must never hold secrets; and because verification is stateless, "
        "tokens are kept short-lived and backed by a refresh flow rather than revoked directly."))
    s.append(P(
        "<b>OAuth 2.0.</b> Where third-party applications are involved, an authorization server "
        "issues scoped access tokens so the third party never sees the user's password at all. For "
        "a MoMo system a budgeting app could be granted "
        "<font face='Courier'>transactions:read</font> and nothing more — able to list transactions "
        "but never delete one — and the user could revoke that single app at any time without "
        "changing their own password. The cost is significantly greater complexity and the need to "
        "run an authorization server, which is justified for multi-client access but excessive for "
        "one trusted internal client."))
    s.append(P(
        "<b>Supporting measures.</b> Whichever scheme is chosen, HTTPS/TLS is mandatory, passwords "
        "should be stored salted and hashed with bcrypt or Argon2, login endpoints should be rate "
        "limited, and per-user accounts with roles should replace the single shared login so that "
        "actions are attributable."))

    s.append(PageBreak())

    # ---------------------------------------------------- 6. DSA results ---
    s.append(P("6. Data Structures and Algorithms Comparison", "h1"))
    s.append(P(
        "Two strategies for finding a transaction by id were implemented in "
        "<font face='Courier'>dsa/dsa_comparison.py</font> and timed against each other:"))
    s.extend(bullets([
        "<b>Linear search</b> — walk the list of transactions one record at a time, comparing each "
        "id until the target is found.",
        "<b>Dictionary lookup</b> — build a dictionary mapping id to transaction once, then fetch "
        "the target by key.",
    ]))
    s.append(P(
        f"Both were run against all 1,691 records for <b>20 target ids</b> spaced evenly across the "
        f"dataset, with <b>1,000 repetitions per measurement</b> using Python's "
        f"<font face='Courier'>timeit</font> module. Each result was asserted equal across the two "
        f"methods so the comparison is like for like. Alongside wall-clock time the benchmark also "
        f"counts the <b>number of record comparisons</b> each strategy performs, measured in a "
        f"separate pass so the counter never distorts the timings. That count matters because it is "
        f"independent of how fast this particular machine happens to be."))

    data = [["Target id", "Position", "Linear (\u00b5s)", "Dict (\u00b5s)",
             "Speed-up", "Linear cmps", "Dict cmps"]]
    for tid, pos, lin, dct, spd, lcmp, dcmp in rows:
        data.append([tid, pos, lin, dct, f"{spd}x", lcmp, dcmp])
    data.append(["AVERAGE", "", lin_avg, dict_avg, f"{speedup}x",
                 lin_cmps_avg, dict_cmps_avg])
    t = grid(data, [2.1 * cm, 2.0 * cm, 2.4 * cm, 2.2 * cm, 2.2 * cm, 2.7 * cm, 2.4 * cm],
             align_right=(0, 1, 2, 3, 4, 5, 6))
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dce7f2")),
    ]))
    s.append(t)
    s.append(Spacer(1, 4))
    s.append(P("Table 4 — Measured lookup cost. Full output is captured in "
               "<font face='Courier'>screenshots/dsa_results.txt</font>.", "caption"))

    s.append(P("6.1 Why dictionary lookup is faster", "h2"))
    s.append(P(
        f"The table shows the pattern clearly. Linear search costs rise steadily with how deep the "
        f"record sits in the list — roughly {rows[0][2]} \u00b5s for the first record against "
        f"{rows[-1][2]} \u00b5s for one near the end — because the number of comparisons grows in "
        f"direct proportion to the position. That is <b>O(n)</b> behaviour. Dictionary lookup, by "
        f"contrast, stays flat at about {dict_avg} \u00b5s no matter where the record sits, which is "
        f"<b>O(1)</b>."))
    s.append(P(
        f"The comparison counts make the same point without depending on machine speed at all. "
        f"Linear search needs exactly as many comparisons as the record's position \u2014 1 for the "
        f"first record and {rows[-1][5]} for the last one sampled, averaging {lin_cmps_avg} across "
        f"the 20 targets. Dictionary lookup needs {dict_cmps_avg} comparison every single time, "
        f"regardless of position or dataset size. A faster processor would shrink both timing "
        f"columns, but it would not change these counts \u2014 which is what makes the difference "
        f"structural rather than incidental."))
    s.append(P(
        "The reason is that a dictionary does not search at all. Python hashes the key once, and "
        "that hash tells it directly which bucket the value lives in, so the work done is the same "
        "whether the dictionary holds ten records or ten thousand. Linear search has no such "
        "shortcut and must compare records one by one until it finds a match. Averaged across the "
        f"20 sampled ids, the dictionary is about <b>{speedup}x faster</b> on this dataset, doing "
        f"{dict_cmps_avg} comparison where linear search does {lin_cmps_avg}."))
    s.append(P(
        "The trade-off is memory and setup: the dictionary has to be built first, an O(n) pass, and "
        "it holds an extra reference per record. That cost is paid once and repaid on every "
        "subsequent lookup, which is why the API itself stores transactions in a dictionary keyed "
        "by id — making every GET, PUT and DELETE by id an O(1) operation."))

    s.append(P("6.2 Other structures that would improve on linear search", "h2"))
    s.extend(bullets([
        "<b>Binary search</b> on an id-sorted list — <b>O(log n)</b>, halving the search space each "
        "step. It needs no extra memory beyond keeping the list sorted, but every insertion must "
        "preserve that order.",
        "<b>B-tree or database index</b> — how a real database indexes a primary key. It keeps "
        "lookups fast while also supporting range queries a hash cannot answer, such as \"all "
        "transactions between two dates\".",
        "<b>Hash index on secondary fields</b> — building the same id-to-record trick for "
        "<font face='Courier'>sender</font> or <font face='Courier'>transaction_type</font> would "
        "extend O(1) lookup beyond the primary key.",
    ]))

    # ---------------------------------------------------- 7. testing -------
    s.append(P("7. Testing and Validation", "h1"))
    s.append(P(
        "The API was tested end to end with <font face='Courier'>curl</font> via "
        "<font face='Courier'>screenshots/run_tests.sh</font>, which exercises nine cases and "
        "captures the full request/response transcript to "
        "<font face='Courier'>screenshots/api_test_results.txt</font>."))
    tests = [["#", "Test case", "Expected"]]
    tests += [
        ["1", "GET /transactions with valid credentials", "200"],
        ["2", "GET /transactions/1 with valid credentials", "200"],
        ["3", "GET /transactions with wrong password", "401"],
        ["4", "GET /transactions with no credentials", "401"],
        ["5", "POST /transactions creating a record", "201"],
        ["6", "PUT on the newly created record", "200"],
        ["7", "DELETE the newly created record", "200"],
        ["8", "GET the deleted record", "404"],
        ["9", "POST with a non-numeric amount", "400"],
    ]
    s.append(grid(tests, [1.0 * cm, 10.8 * cm, 2.1 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 5 — Test cases. All nine produced the expected status code.", "caption"))
    s.append(P(
        "The script reads the server-assigned id back from the POST response rather than assuming "
        "one, so the whole suite can be re-run repeatedly against a running server without the "
        "update, delete and 404 cases drifting out of step."))

    # ---------------------------------------------------- 8. conclusion ----
    s.append(P("8. Conclusion", "h1"))
    s.append(P(
        "The system parses all 1,691 SMS records into structured JSON, serves them through five "
        "CRUD endpoints built on the Python standard library, and protects every endpoint with "
        "Basic Authentication that correctly returns 401 for missing, malformed and incorrect "
        "credentials. The DSA comparison demonstrates in measured numbers why the API stores its "
        f"records in a dictionary: an average {speedup}x speed-up over linear search, and a lookup "
        "cost that stays flat as the dataset grows."))
    s.append(P(
        "The main limitation is the authentication scheme itself. Because Base64 is encoding rather "
        "than encryption, the password is effectively sent in the clear on every single request, "
        "with no expiry, no revocation and no per-user identity. The next step for this project "
        "would be to serve the API over HTTPS and replace Basic Auth with short-lived JWTs, adding "
        "OAuth 2.0 scopes once third-party applications need access to the data."))

    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
