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
        "An API is the way every client application gets to the data behind it, which means it is "
        "also the way anyone else would get to that data if it were left open. For a mobile money "
        "system that data is about as sensitive as it gets. It says how much money moved, who sent "
        "it, who received it, their phone numbers, and what the balance was afterwards. Someone who "
        "can reach an unprotected version of this API can read a customer's entire financial "
        "history, and if the write endpoints are open too, they can change it or delete it."))
    s.append(P(
        "When people talk about securing an API they usually mean three different things, and it "
        "helps to keep them apart. <b>Authentication</b> is about working out who is making the "
        "request. <b>Authorization</b> is about deciding whether that person is allowed to do the "
        "particular thing they are asking for. <b>Confidentiality</b> is about stopping anyone else "
        "from reading the exchange while it crosses the network, which is what HTTPS gives you."))
    s.append(P(
        "You need all three, because any one of them on its own leaves a hole. Checking a password "
        "carefully does not help if that password is being sent in a form anyone can read. "
        "Encrypting the connection does not help if every user who logs in is allowed to delete "
        "everything. This project covers the first of the three, using HTTP Basic Authentication, "
        "because that is what the assignment asked for. Every endpoint turns away requests that are "
        "not authenticated with a 401 response. Section 5 goes through where that approach falls "
        "short, which is further than we expected when we started."))

    # -------------------------------------------------- 2. system overview --
    s.append(P("2. System Overview and Data Parsing", "h1"))
    s.append(P(
        "The file we were given, <font face='Courier'>modified_sms_v2.xml</font>, is an SMS backup "
        "from an MTN Mobile Money account. It holds 1,691 "
        "<font face='Courier'>&lt;sms&gt;</font> elements. The catch is that the useful information "
        "is not sitting in neat XML fields. It is inside the <font face='Courier'>body</font> "
        "attribute as ordinary English sentences, the same text a person would read on their phone. "
        "So the parser cannot just pull out tags. It has to read meaning out of prose."))
    s.append(P(
        "We handled that in <font face='Courier'>dsa/parse_xml.py</font> with a list of regular "
        "expressions, each one labelled with the kind of transaction it matches. Every SMS body is "
        "tested against the patterns in order, and the first one that matches decides the "
        "transaction type and pulls out the pieces we want: the amount, the fee, the new balance, "
        "the sender, the receiver, the account and the transaction id."))
    s.append(P(
        "A few small things needed cleaning up along the way. Amounts appear in the messages written "
        "as \"12,500\", so they get their commas stripped and become numbers rather than staying as "
        "text. Dates get converted to ISO-8601. Some messages carry no readable time at all, and "
        "for those we fall back to the epoch timestamp stored on the element itself."))
    s.append(P("Here is how the 1,691 records break down:"))

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
    s.append(P("Table 1 — How many records of each type. Every record in the file matched one of "
               "these, so nothing was left unrecognised.", "caption"))
    s.append(P(
        "The parser saves all of this to <font face='Courier'>data/transactions.json</font> as a "
        "list of dictionaries, which is exactly the shape the API needs in order to serve it."))

    s.append(PageBreak())

    # ------------------------------------------------ 3. endpoint docs -----
    s.append(P("3. API Endpoint Documentation", "h1"))
    s.append(P(
        "The API is written in plain Python using <font face='Courier'>http.server</font>, with no "
        "outside libraries. It gives you five endpoints covering the usual create, read, update and "
        "delete operations. The records live in memory in a dictionary keyed by id, which is why "
        "looking one up is quick no matter how many there are. Section 6 covers that properly. "
        "<b>Every one of these endpoints needs a username and password.</b>"))

    ep = [["Method", "Endpoint", "What it does", "Success"]]
    ep += [
        ["GET", "/transactions", "Lists every transaction", "200"],
        ["GET", "/transactions/{id}", "Gets one transaction", "200"],
        ["POST", "/transactions", "Adds a new one", "201"],
        ["PUT", "/transactions/{id}", "Updates an existing one", "200"],
        ["DELETE", "/transactions/{id}", "Deletes one", "200"],
    ]
    s.append(grid(ep, [1.8 * cm, 4.4 * cm, 6.0 * cm, 1.6 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 2 — The five endpoints.", "caption"))

    s.append(P("3.1 Examples", "h2"))

    s.append(P("<b>GET /transactions/1</b> gets a single record.", "body"))
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

    s.append(P("<b>POST /transactions</b> adds a record. You have to send "
               "<font face='Courier'>transaction_type</font> and "
               "<font face='Courier'>amount</font>, and the server picks the id.", "body"))
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

    s.append(P("<b>PUT /transactions/1692</b> changes a record. Send only the fields you want to "
               "change and the rest stay as they were.", "body"))
    s.append(P("$ curl -u admin:momo2025 -X PUT http://localhost:8000/transactions/1692 \\<br/>"
               "&nbsp;&nbsp;-H \"Content-Type: application/json\" -d '{\"amount\":9900}'"
               "<br/><br/>HTTP/1.0 200 OK", "code"))

    s.append(P("<b>DELETE /transactions/1692</b> removes a record, and hands back what it deleted "
               "so you can see what has gone.", "body"))
    s.append(P("$ curl -u admin:momo2025 -X DELETE http://localhost:8000/transactions/1692"
               "<br/><br/>HTTP/1.0 200 OK<br/>"
               "{ \"message\": \"Transaction 1692 deleted\", \"deleted\": { ... } }", "code"))

    s.append(P("And this is what you get with the wrong password.", "body"))
    s.append(P("$ curl -i -u admin:wrongpassword http://localhost:8000/transactions<br/><br/>"
               "HTTP/1.0 401 Unauthorized<br/>"
               "WWW-Authenticate: Basic realm=\"MoMo Transactions API\"<br/><br/>"
               "{ \"error\": \"Unauthorized: invalid username or password\", \"status\": 401 }",
               "code"))

    s.append(P("3.2 Error codes", "h2"))
    errs = [["Code", "Name", "When you get it"]]
    errs += [
        ["200", "OK", "A GET, PUT or DELETE worked"],
        ["201", "Created", "A POST worked"],
        ["400", "Bad Request", "Broken JSON, a missing required field, a field we do not "
                               "recognise, or an amount that is negative or not a number"],
        ["401", "Unauthorized", "No credentials, broken credentials, or the wrong password"],
        ["404", "Not Found", "That id does not exist, or that URL is not one of ours"],
    ]
    s.append(grid(errs, [1.5 * cm, 2.6 * cm, 9.7 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 3 — Error codes. Every error comes back in the same shape, "
               "<font face='Courier'>{\"error\": ..., \"status\": ...}</font>, so a client can "
               "handle them the same way each time. The full documentation is in "
               "<font face='Courier'>docs/api_docs.md</font>.", "caption"))

    s.append(PageBreak())

    # ---------------------------------------------- 4. auth implementation --
    s.append(P("4. How We Implemented the Login", "h1"))
    s.append(P(
        "Every request has to carry an <font face='Courier'>Authorization</font> header holding the "
        "username and password joined with a colon and base64-encoded. The handler decodes that and "
        "checks both halves before any of the routing code runs, so there is no way to reach an "
        "endpoint without passing the check first."))
    s.append(P("Authorization: Basic YWRtaW46bW9tbzIwMjU=", "code"))
    s.append(P("Three details in our implementation are worth pointing out:", "body"))
    s.extend(bullets([
        "We compare the credentials with <font face='Courier'>hmac.compare_digest()</font> instead "
        "of <font face='Courier'>==</font>. A normal comparison stops at the first character that "
        "does not match, so checking a nearly-correct password takes very slightly longer than "
        "checking a completely wrong one. That difference is tiny but measurable, and an attacker "
        "can use it to work out a password one character at a time. "
        "<font face='Courier'>compare_digest()</font> always takes the same time, so there is "
        "nothing to measure.",
        "The credentials are not written into the code. They come from the "
        "<font face='Courier'>API_USERNAME</font> and <font face='Courier'>API_PASSWORD</font> "
        "environment variables and only fall back to defaults for development, so the real password "
        "never has to be committed to git.",
        "Every way of failing returns a 401 rather than a crash. A missing header, a header that is "
        "not <font face='Courier'>Basic</font>, base64 that will not decode, and a simply wrong "
        "password are all handled, and all answered with a 401 plus a "
        "<font face='Courier'>WWW-Authenticate</font> header telling the client what to send.",
    ]))

    # ------------------------------------------------- 5. reflection -------
    s.append(P("5. Reflection: Why Basic Auth Is Weak", "h1"))
    s.append(P(
        "We are confident the Basic Auth above is implemented properly. The scheme itself is still "
        "the weakest part of the whole project, and it is worth being honest about why."))

    s.append(P("5.1 Base64 is not encryption", "h2"))
    s.append(P(
        "This is the main issue, and it is easy to miss because the word \"encoded\" sounds like it "
        "means something. It does not. Base64 uses no key and no secret, so anybody can undo it:"))
    s.append(P("$ echo -n 'admin:momo2025' | base64<br/>"
               "YWRtaW46bW9tbzIwMjU=<br/><br/>"
               "$ echo 'YWRtaW46bW9tbzIwMjU=' | base64 --decode<br/>"
               "admin:momo2025", "code"))
    s.append(P(
        "So the password is really being sent in plain text. Over plain HTTP, anybody who can see "
        "the traffic reads it straight off the wire. That might be someone else on the same coffee "
        "shop wifi, a router that has been tampered with, or the internet provider. Basic Auth is "
        "only acceptable at all if the connection is HTTPS, and even then the problems below still "
        "apply."))

    s.append(P("5.2 The other problems", "h2"))
    s.extend(bullets([
        "<b>The password goes out on every request.</b> HTTP does not remember anything between "
        "requests, so the client resends it each time. Load a page that makes thirty API calls and "
        "the password has crossed the network thirty times. Each one is a chance for it to end up "
        "in a proxy log or an error report, and because it is the real password rather than a "
        "temporary token, one leak is permanent.",
        "<b>It does not expire, and you cannot cancel it.</b> A Basic Auth password stays valid "
        "until a person changes it, and changing it is also the only way to shut it down. If five "
        "apps share the login, changing it breaks all five, including the four that were fine.",
        "<b>Everyone shares one account.</b> If a record gets deleted the log says \"admin\" did "
        "it, not which person, so there is no real audit trail. A read-only mobile app also ends up "
        "holding a password that can delete every record in the database.",
        "<b>Nothing slows down guessing.</b> We have no rate limiting, no lockout after failed "
        "attempts and no second factor, so an attacker can try passwords as fast as the server "
        "answers them.",
    ]))

    s.append(P("5.3 What we would use instead", "h2"))
    s.append(P(
        "<b>JWT.</b> The client sends its password once, to a login endpoint, and gets back a "
        "signed token that it sends from then on as "
        "<font face='Courier'>Authorization: Bearer &lt;token&gt;</font>. The token carries the "
        "user's id, their role and an expiry time, and it is signed with a key only the server "
        "knows. That fixes most of what is wrong above. The real password crosses the network once "
        "instead of constantly, tokens expire on their own so a stolen one is useful only briefly, "
        "and because the token says who the user is you can keep a proper audit log and give a "
        "read-only app a read-only token. The catch is that a JWT is signed but not encrypted, so "
        "anyone holding it can read what is inside and you must never put secrets in there. And "
        "since the server only checks the signature rather than looking anything up, you cannot "
        "easily cancel a token before it expires, which is why access tokens are usually kept short "
        "and paired with a refresh token."))
    s.append(P(
        "<b>OAuth 2.0.</b> This is the right answer once other people's applications are involved. "
        "Instead of a third-party app holding the user's password, a separate authorization server "
        "issues tokens with scopes attached. A budgeting app that wants to show someone their MoMo "
        "spending could be given a token scoped to <font face='Courier'>transactions:read</font> "
        "and nothing else. It could list transactions and that is all, and the user could cut that "
        "one app off whenever they liked without changing their password or affecting anything else "
        "they use. The downside is that it is a lot more work and needs an authorization server "
        "running, which is overkill for a project with one trusted client."))
    s.append(P(
        "<b>Either way,</b> the connection has to be HTTPS, because without it every scheme here "
        "leaks its password or token in transit. Passwords should be stored salted and hashed with "
        "something slow like bcrypt or Argon2, the login endpoint should be rate limited, and each "
        "person should have their own account with a role rather than everyone sharing one."))

    s.append(PageBreak())

    # ---------------------------------------------------- 6. DSA results ---
    s.append(P("6. Comparing Linear Search and Dictionary Lookup", "h1"))
    s.append(P(
        "We built two ways of finding a transaction by its id in "
        "<font face='Courier'>dsa/dsa_comparison.py</font> and timed them against each other:"))
    s.extend(bullets([
        "<b>Linear search</b> walks the list of transactions one record at a time, checking each id "
        "until it finds the one it wants.",
        "<b>Dictionary lookup</b> builds a dictionary of id to transaction once, then fetches the "
        "record by key.",
    ]))
    s.append(P(
        "We ran both against all 1,691 records for <b>20 different ids</b> spread evenly across the "
        "dataset, repeating each measurement <b>1,000 times</b> with Python's "
        "<font face='Courier'>timeit</font> module. We also checked that both methods returned the "
        "same record every time, so we know we were comparing like with like. On top of the timings "
        "we counted how many record comparisons each method actually performs, done in a separate "
        "pass so the counting never slows down the timed run. That count turned out to be the more "
        "useful number, for reasons we get to below."))

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
    s.append(P("Table 4 — What we measured. The full output is saved in "
               "<font face='Courier'>screenshots/dsa_results.txt</font>.", "caption"))

    s.append(P("6.1 Why the dictionary is faster", "h2"))
    s.append(P(
        f"The pattern in the table is hard to miss. Linear search gets steadily slower the further "
        f"into the list the record sits, going from about {rows[0][2]} \u00b5s for the very first "
        f"record up to {rows[-1][2]} \u00b5s for one near the end. That is because it has to check "
        f"every record it passes on the way, and that is what O(n) means in practice. The "
        f"dictionary stays at roughly {dict_avg} \u00b5s the whole way down the table no matter "
        f"where the record is, which is O(1)."))
    s.append(P(
        "The reason is that a dictionary does not really search at all. Python runs the id through "
        "a hash function, and the answer tells it exactly which bucket the record is sitting in, so "
        "it goes straight there. It does the same amount of work whether the dictionary holds ten "
        "records or ten thousand. Linear search has no such shortcut. It has to compare records one "
        "by one until it gets a match."))
    s.append(P(
        f"The comparison counts show the same thing without depending on the computer at all, which "
        f"is why we added them. Linear search needs exactly as many comparisons as the record's "
        f"position: 1 for the first record, {rows[-1][5]} for the last one we sampled, and "
        f"{lin_cmps_avg} on average across the twenty. The dictionary needs "
        f"{dict_cmps_avg} comparison every single time. A faster laptop would shrink both timing "
        f"columns, but it would not change these counts by one. The difference is in how the two "
        f"methods work, not in how quick the machine is."))
    s.append(P(
        f"Averaged over the twenty ids the dictionary came out about <b>{speedup}x faster</b>. It "
        f"is not free, though. You have to build the dictionary first, which is one pass through "
        f"the data, and it keeps an extra reference for every record. You pay that once and get it "
        f"back on every lookup afterwards, which is exactly why the API itself stores its "
        f"transactions in a dictionary. It means getting, updating or deleting a record by id is an "
        f"O(1) operation instead of a scan."))

    s.append(P("6.2 What else could we have used?", "h2"))
    s.append(P("A dictionary is not the only thing that beats a linear scan:"))
    s.extend(bullets([
        "<b>Binary search</b> on a list kept sorted by id. Each step throws away half of what is "
        "left, so it is O(log n). It needs no extra memory, but the list has to stay sorted, which "
        "means every insertion costs something.",
        "<b>A B-tree, or a database index.</b> This is what a real database uses for a primary key. "
        "It stays fast and it can also answer questions a hash cannot, like asking for every "
        "transaction between two dates.",
        "<b>A second dictionary on a different field</b>, say <font face='Courier'>sender</font> or "
        "<font face='Courier'>transaction_type</font>. Same trick, just applied to something other "
        "than the id, if that is what you need to search on.",
    ]))

    # ---------------------------------------------------- 7. testing -------
    s.append(P("7. Testing and Validation", "h1"))
    s.append(P(
        "We tested the API end to end with <font face='Courier'>curl</font>, using "
        "<font face='Courier'>screenshots/run_tests.sh</font>. It runs nine cases and saves the "
        "whole request and response transcript to "
        "<font face='Courier'>screenshots/api_test_results.txt</font>."))
    tests = [["#", "What we tested", "Expected"]]
    tests += [
        ["1", "GET /transactions with the right credentials", "200"],
        ["2", "GET /transactions/1 with the right credentials", "200"],
        ["3", "GET /transactions with the wrong password", "401"],
        ["4", "GET /transactions with no credentials at all", "401"],
        ["5", "POST /transactions creating a record", "201"],
        ["6", "PUT on the record we had just created", "200"],
        ["7", "DELETE the record we had just created", "200"],
        ["8", "GET that record again after deleting it", "404"],
        ["9", "POST with an amount that is not a number", "400"],
    ]
    s.append(grid(tests, [1.0 * cm, 10.8 * cm, 2.1 * cm]))
    s.append(Spacer(1, 4))
    s.append(P("Table 5 — The nine test cases. All of them returned the status code we expected.",
               "caption"))
    s.append(P(
        "One small thing we changed part way through: the script now reads the new id out of the "
        "POST response instead of assuming what it will be. Before that, running the tests twice "
        "against the same server made the update, delete and 404 cases fail, because the id had "
        "moved on and the script was still looking for the old one."))

    # ---------------------------------------------------- 8. conclusion ----
    s.append(P("8. Conclusion", "h1"))
    s.append(P(
        "The system reads all 1,691 SMS records out of the XML and turns them into structured JSON, "
        "serves them through five endpoints built on nothing but the Python standard library, and "
        "puts Basic Authentication in front of all of them, returning 401 for credentials that are "
        "missing, malformed or simply wrong. The search comparison gave us a real reason for a "
        f"design decision rather than a guess: the dictionary was about {speedup}x faster on "
        "average, and more importantly its cost does not grow as the dataset does."))
    s.append(P(
        "The weakest part is the authentication, and that is worth saying plainly. Because base64 "
        "is encoding rather than encryption, the password is effectively sent in the clear on every "
        "request, it never expires, it cannot be revoked, and there is no way to tell one user from "
        "another. If this were going to be used for real, the next steps would be to put it behind "
        "HTTPS and move to short-lived JWTs, then add OAuth 2.0 scopes later if other people's "
        "applications ever needed access to the data."))

    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
