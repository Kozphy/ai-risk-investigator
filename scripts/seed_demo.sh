#!/usr/bin/env bash
set -euo pipefail
API="${API_URL:-http://localhost:8000}"

email="${DEMO_EMAIL:-auditor@example.com}"
password="${DEMO_PASSWORD:-ChangeMe123!}"

curl -sS -X POST "$API/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$email\",\"password\":\"$password\",\"full_name\":\"Demo Auditor\",\"organization\":\"Kozphy Demo\"}" || true

TOKEN=$(curl -sS -X POST "$API/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$email\",\"password\":\"$password\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sS -X POST "$API/api/v1/knowledge" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@examples/knowledge/gdpr_excerpt.txt" \
  -F "title=GDPR Excerpts" \
  -F "source_type=regulation" \
  -F "framework=GDPR"

curl -sS -X POST "$API/api/v1/knowledge" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@examples/knowledge/iso27001_excerpt.txt" \
  -F "title=ISO 27001 Excerpts" \
  -F "source_type=control_framework" \
  -F "framework=ISO 27001"

DOC=$(curl -sS -X POST "$API/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@examples/documents/sample_vendor_contract.txt" \
  -F "document_type=contract")

DOC_ID=$(python -c "import json,sys; print(json.loads('''$DOC''')['id'])")
curl -sS -X POST "$API/api/v1/analyses" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"document_id\":\"$DOC_ID\"}"

echo "Seeded knowledge + sample analysis for $email"
