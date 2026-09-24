"""Parse the MoMo SMS XML export into normalised JSON transaction objects."""

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_XML = os.path.join(BASE_DIR, "data", "modified_sms_v2.xml")
DEFAULT_JSON = os.path.join(BASE_DIR, "data", "transactions.json")

AMOUNT = r"([\d,]+(?:\.\d+)?)"


def _num(value):
    """Turn '12,500' or '12500.00' into a float, or None when absent."""
    if value is None:
        return None
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _iso(value):
    """Normalise '2024-05-10 16:30:51' into an ISO-8601 string."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S").isoformat()
    except ValueError:
        return None


def _epoch_iso(value):
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


RULES = [
    # (category, regex, field -> group mapping)
    (
        "incoming_money",
        re.compile(
            r"You have received " + AMOUNT + r" RWF from (?P<sender>.+?) \((?P<sender_phone>[^)]*)\).*?"
            r"at (?P<ts>[\d\-]+ [\d:]+).*?new balance:\s*(?P<balance>[\d,]+) RWF\. "
            r"Financial Transaction Id: (?P<txid>\d+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "payment_to_code_holder",
        re.compile(
            r"TxId:\s*(?P<txid>\d+)\. Your payment of " + AMOUNT + r" RWF to (?P<receiver>.+?) (?P<receiver_code>\d+) "
            r"has been completed at (?P<ts>[\d\-]+ [\d:]+)\. Your new balance: (?P<balance>[\d,]+) RWF\. "
            r"Fee was (?P<fee>[\d,]+) RWF",
        ),
        {"amount": 1},
    ),
    (
        "transfer_to_mobile",
        re.compile(
            r"\*165\*S\*" + AMOUNT + r" RWF transferred to (?P<receiver>.+?) \((?P<receiver_phone>[^)]*)\) "
            r"from (?P<account>\d+) at (?P<ts>[\d\-]+ [\d:]+).*?Fee was:\s*(?P<fee>[\d,]+) RWF\. "
            r"New balance:\s*(?P<balance>[\d,]+) RWF",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "bank_deposit",
        re.compile(
            r"bank deposit of " + AMOUNT + r" RWF has been added to your mobile money account "
            r"at (?P<ts>[\d\-]+ [\d:]+)\. Your NEW BALANCE :(?P<balance>[\d,]+) RWF",
        ),
        {"amount": 1},
    ),
    (
        # Statement-style deposit line, e.g. "1) 2024-08-23 DEPOSIT RWF 25000 Receiver: ..."
        "bank_deposit",
        re.compile(
            r"^\d+\)\s*[\d\-]+\s+DEPOSIT RWF\s+" + AMOUNT + r"\s+Receiver:\s*(?P<account>\d*)",
        ),
        {"amount": 1},
    ),
    (
        "bill_or_airtime_payment",
        re.compile(
            r"\*162\*TxId:(?P<txid>\d+)\*S\*Your payment of " + AMOUNT + r" RWF to (?P<receiver>.+?) with token\s*"
            r"(?P<token>\S*)\s*has been completed at (?P<ts>[\d\-]+ [\d:]+)\. Fee was (?P<fee>[\d,]+) RWF\. "
            r"Your new balance: (?P<balance>[\d,]+) RWF",
        ),
        {"amount": 1},
    ),
    (
        "third_party_payment",
        re.compile(
            r"\*164\*S\*Y'ello,A transaction of " + AMOUNT + r" RWF by (?P<receiver>.+?) on your MOMO account "
            r"was successfully completed at (?P<ts>[\d\-]+ [\d:]+).*?new balance:(?P<balance>[\d,]+) RWF\. "
            r"Fee was (?P<fee>[\d,]+) RWF\. Financial Transaction Id: (?P<txid>\d+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "withdrawal",
        re.compile(
            r"You (?P<sender>.+?) \((?P<sender_phone>[^)]*)\) have via agent: (?P<receiver>.+?) "
            r"\((?P<receiver_phone>[^)]*)\), withdrawn " + AMOUNT + r" RWF from your mobile money account: "
            r"(?P<account>\d+) at (?P<ts>[\d\-]+ [\d:]+).*?new balance: (?P<balance>[\d,]+) RWF\. "
            r"Fee paid: (?P<fee>[\d,]+) RWF.*?Financial Transaction Id: (?P<txid>\d+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "bank_transfer",
        re.compile(
            r"You have transferred " + AMOUNT + r" RWF to (?P<receiver>.+?) \((?P<receiver_phone>[^)]*)\) "
            r"from your mobile money account (?P<account>\S+).*?at (?P<ts>[\d\-]+ [\d:]+).*?"
            r"Financial Transaction Id: (?P<txid>\d+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "merchant_payment",
        re.compile(
            r"Your payment of " + AMOUNT + r" RWF to (?P<receiver>.+?) \((?P<receiver_phone>[^)]*)\) "
            r"has been completed at (?P<ts>[\d\-]+ [\d:]+).*?Your new balance: (?P<balance>[\d,]+) RWF\. "
            r"Fee was (?P<fee>[\d,]+) RWF.*?Financial Transaction Id: (?P<txid>\d+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "reversal",
        re.compile(
            r"transaction to (?P<receiver>.+?) \((?P<receiver_phone>[^)]*)\) with " + AMOUNT + r" RWF",
        ),
        {"amount": 1},
    ),
    (
        "failed_transaction",
        re.compile(
            r"transaction with amount " + AMOUNT + r" RWF for (?P<receiver>.+?) with message.*?"
            r"failed at (?P<ts>[\d\-]+ [\d:]+)",
            re.S,
        ),
        {"amount": 1},
    ),
    (
        "failed_transaction",
        re.compile(
            r"\*143\*TxId:(?P<txid>\d+)\*S\*Your payment of " + AMOUNT + r" RWF to (?P<receiver>.+?) "
            r"with token\s*(?P<token>\S*)\s*has failed at (?P<ts>[\d\-]+ [\d:]+)",
        ),
        {"amount": 1},
    ),
    (
        "bundle_purchase_notice",
        re.compile(r"Yello!Umaze kugura (?P<bundle>.+?) igura " + AMOUNT + r" RWF"),
        {"amount": 2},
    ),
    ("otp", re.compile(r"one-time password is :(?P<token>\d+)"), {}),
]


def classify(body):
    """Match an SMS body against the known MoMo message formats."""
    for category, pattern, extra in RULES:
        match = pattern.search(body)
        if not match:
            continue
        groups = match.groupdict()
        amount_index = extra.get("amount")
        amount = _num(match.group(amount_index)) if amount_index else None
        return category, groups, amount
    return "other", {}, None


def parse_sms(element, index):
    """Convert one <sms> element into a transaction dictionary."""
    body = (element.get("body") or "").strip()
    category, groups, amount = classify(body)

    timestamp = _iso(groups.get("ts")) or _epoch_iso(element.get("date"))

    return {
        "id": index,
        "transaction_type": category,
        "amount": amount,
        "fee": _num(groups.get("fee")),
        "new_balance": _num(groups.get("balance")),
        "sender": (groups.get("sender") or "").strip() or None,
        "sender_phone": (groups.get("sender_phone") or "").strip() or None,
        "receiver": (groups.get("receiver") or "").strip() or None,
        "receiver_phone": (groups.get("receiver_phone") or "").strip() or None,
        "receiver_code": groups.get("receiver_code"),
        "account": groups.get("account"),
        "financial_transaction_id": groups.get("txid"),
        "timestamp": timestamp,
        "readable_date": element.get("readable_date"),
        "service_center": element.get("service_center"),
        "address": element.get("address"),
        "body": body,
    }


def parse_file(xml_path=DEFAULT_XML):
    """Parse the whole XML export and return a list of transaction dictionaries."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return [parse_sms(sms, i) for i, sms in enumerate(root.findall("sms"), start=1)]


def save_json(transactions, json_path=DEFAULT_JSON):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(transactions, handle, indent=2, ensure_ascii=False)
    return json_path


def load_transactions(json_path=DEFAULT_JSON, xml_path=DEFAULT_XML):
    """Load cached JSON if present, otherwise parse the XML and cache it."""
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as handle:
            return json.load(handle)
    transactions = parse_file(xml_path)
    save_json(transactions, json_path)
    return transactions


if __name__ == "__main__":
    records = parse_file()
    path = save_json(records)

    counts = {}
    for record in records:
        counts[record["transaction_type"]] = counts.get(record["transaction_type"], 0) + 1

    print(f"Parsed {len(records)} SMS records -> {path}")
    print("\nRecords per transaction type:")
    for name, total in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {name:<26} {total}")
    print("\nSample record:")
    print(json.dumps(records[0], indent=2))
