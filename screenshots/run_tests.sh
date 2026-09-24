#!/usr/bin/env bash
# Exercises every endpoint plus the authentication failure paths.
# Usage:  bash screenshots/run_tests.sh
set -u

BASE="http://localhost:8000"
AUTH="admin:momo2025"
BAD_AUTH="admin:wrongpassword"

hr() { printf '\n========== %s ==========\n' "$1"; }

hr "1. GET /transactions  (authenticated, truncated)"
curl -s -u "$AUTH" "$BASE/transactions" | head -c 600; echo

hr "2. GET /transactions/1  (authenticated)"
curl -s -i -u "$AUTH" "$BASE/transactions/1"

hr "3. GET /transactions  (WRONG password -> 401)"
curl -s -i -u "$BAD_AUTH" "$BASE/transactions"

hr "4. GET /transactions  (NO credentials -> 401)"
curl -s -i "$BASE/transactions"

hr "5. POST /transactions  (create -> 201)"
CREATED=$(curl -s -u "$AUTH" -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"transaction_type":"incoming_money","amount":7500,"fee":0,"sender":"Chol Deng","receiver":"Test Account","timestamp":"2025-09-19T10:00:00"}')
echo "$CREATED"

# Read the server-assigned id back so the script can be re-run against a live server.
NEW_ID=$(printf '%s' "$CREATED" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p' | head -1)
printf '\n--> server assigned id: %s\n' "$NEW_ID"

hr "6. PUT /transactions/$NEW_ID  (update -> 200)"
curl -s -i -u "$AUTH" -X PUT "$BASE/transactions/$NEW_ID" \
  -H "Content-Type: application/json" \
  -d '{"amount":9900,"receiver":"Updated Account"}'

hr "7. DELETE /transactions/$NEW_ID  (delete -> 200)"
curl -s -i -u "$AUTH" -X DELETE "$BASE/transactions/$NEW_ID"

hr "8. GET /transactions/$NEW_ID  (deleted -> 404)"
curl -s -i -u "$AUTH" "$BASE/transactions/$NEW_ID"

hr "9. POST /transactions  (invalid body -> 400)"
curl -s -i -u "$AUTH" -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"amount":"not-a-number"}'

echo
