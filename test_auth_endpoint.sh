#!/bin/bash

# test_auth_endpoint.sh
# This script tests the token authentication endpoint

API_BASE="http://localhost:8000/api"

echo "========================================="
echo "Testing Bearer Token Authentication"
echo "========================================="
echo ""

# Step 1: Login and get token
echo "Step 1: POST /api/auth/token/"
echo "Sending login request..."
echo ""

RESPONSE=$(curl -s -X POST "$API_BASE/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }')

echo "Response:"
echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract token
TOKEN=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to obtain token. Possible issues:"
  echo "  - Admin user doesn't exist"
  echo "  - Wrong password"
  echo "  - Server not running"
  echo ""
  echo "To create admin user, run:"
  echo "  python manage.py createsuperuser"
  exit 1
fi

echo "✓ Token obtained successfully!"
echo "Token: $TOKEN"
echo ""

# Step 2: Use token in authenticated request
echo "========================================="
echo "Step 2: GET /api/inventory/adjustments/ (with Bearer token)"
echo "Using token in Authorization header..."
echo ""

curl -s -X GET "$API_BASE/inventory/adjustments/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python -m json.tool 2>/dev/null || echo "Response received"

echo ""
echo "✓ Test complete!"
