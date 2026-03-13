# Where to Find the Token Endpoint - Visual Guide

## 📍 Location: HTTP://LOCALHOST:8000/API/AUTH/TOKEN/

Your token endpoint is accessible at:
```
Base URL: http://localhost:8000
API Base: http://localhost:8000/api
Token Endpoint: http://localhost:8000/api/auth/token/
```

---

## 🌐 Finding it in Swagger Documentation

### **Method 1: Swagger UI (Recommended)**

1. **Start your server:**
   ```bash
   source .venv/bin/activate
   python manage.py runserver
   ```

2. **Open in browser:**
   ```
   http://localhost:8000/api/docs/
   ```

3. **Look for the endpoint:**
   - Scroll down or search for "auth"
   - You should see an **"Authentication"** section (collapsed by default)
   - Click to expand it
   - Inside: **POST /api/auth/token/** ← This is your token endpoint
   - Yellow box = POST method (yellow in Swagger = POST)

4. **Try it out in Swagger:**
   - Click on **POST /api/auth/token/**
   - Scroll down to **"Try it out"** button
   - Click the button
   - Fill in the form:
     - **username:** admin
     - **password:** password123
   - Click **"Execute"**
   - You'll see the token in the **Response body**

---

## 📱 Finding it in Postman

### **Method 1: Direct Request**

1. **Create new request in Postman**
2. **Set method to POST**
3. **URL:** `http://localhost:8000/api/auth/token/`
4. **Headers:**
   - Content-Type: application/json
5. **Body (raw JSON):**
   ```json
   {
     "username": "admin",
     "password": "password123"
   }
   ```
6. **Send** → See token in response

### **Method 2: Import from Swagger**

1. Go to `http://localhost:8000/api/schema/` (returns OpenAPI JSON)
2. Copy the JSON
3. In Postman: **File** → **Import** → **Paste Raw Text** → Import
4. The entire API collection appears with `/auth/token/` endpoint included

---

## 🔍 Finding it in Django Admin / URL Router

### **Check Django URLs:**

```bash
# List all URL patterns
python manage.py show_urls

# You should see:
/admin/                                              admin.site.urls
/api/schema/                                         schema
/api/docs/                                           swagger-ui
/api/redoc/                                          redoc
/api/auth/token/                                     api_token_auth  ← HERE
/api/warehouses/                                     warehouse-list-create
/api/inventory/...
...
```

### **Python Shell Check:**

```bash
python manage.py shell
```

```python
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(pattern)
    
# Look for: <URLPattern name='api_token_auth' pattern='^api/auth/token/$'>
```

---

## 🧪 Direct Curl/HTTP Test

### **Using curl (terminal):**

```bash
# Test the endpoint directly
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
  
# Response:
# {
#   "token": "3c0c0fe4d8e8b7a75a4f2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f",
#   "user_id": 1,
#   "email": "admin@example.com"
# }
```

### **Using Python requests:**

```bash
python3 << 'EOF'
import requests
response = requests.post(
    'http://localhost:8000/api/auth/token/',
    json={'username': 'admin', 'password': 'password123'}
)
print(response.json())
EOF
```

### **Using the automated test:**

```bash
cd /home/santos/Documents/KingKuntaEcommerce

# Python test (detailed output)
python test_auth.py

# Or bash script
bash test_auth_endpoint.sh
```

---

## 🗂️ File Structure - Where Code Is Located

```
KingKuntaEcommerce/
├── KingKuntaEcommerce/
│   ├── settings.py              ← REST_FRAMEWORK config
│   ├── urls.py                  ← Include 'api/', include('core.urls')
│   └── ...
│
├── core/
│   ├── urls.py                  ← path('auth/token/', CustomAuthToken)
│   ├── views.py                 ← class CustomAuthToken(ObtainAuthToken)
│   └── ...
│
├── test_auth.py                 ← Test script (run this!)
├── test_auth_endpoint.sh         ← Bash test script
├── AUTH_QUICK_START.md          ← Quick reference
└── FRONTEND_AUTH_GUIDE.md       ← Complete frontend examples
```

---

## 🔗 URL Resolution Chain

Here's how Django routes your request:

```
Request: POST /api/auth/token/
         ↓
KingKuntaEcommerce/urls.py
  path('api/', include('core.urls'))
         ↓
core/urls.py
  path('auth/token/', CustomAuthToken.as_view(), name='api_token_auth')
         ↓
core/views.py
  class CustomAuthToken(ObtainAuthToken):
    def post(self, request, ...):
      # Generate and return token
```

---

## ✅ Verification Checklist

- [ ] Server running: `python manage.py runserver` (shows "Starting development server...")
- [ ] Can access `http://localhost:8000/` (Django home page)
- [ ] Can access `http://localhost:8000/api/` (REST framework root)
- [ ] Can access `http://localhost:8000/api/docs/` (Swagger UI)
- [ ] Can access `http://localhost:8000/api/auth/token/` in Swagger UI
- [ ] POST to `/api/auth/token/` returns token (not 404 or 500)
- [ ] Token can be used with `Authorization: Bearer <token>` header

---

## 🐛 Common Issues & Solutions

### **Issue: 404 Not Found on /api/auth/token/**

**Cause:** URL not registered or server not running

**Solution:**
```bash
# Make sure server is running
python manage.py runserver

# Check URLs are correctly configured
python manage.py show_urls | grep auth

# Restart server (sometimes Django needs reloading)
# Stop server (Ctrl+C) and start again
```

---

### **Issue: 401 Unauthorized**

**Cause:** Invalid credentials

**Solution:**
```bash
# Create/verify admin user
python manage.py createsuperuser
# Username: admin
# Password: password123 (or your choice)
```

---

### **Issue: Endpoint not in Swagger UI**

**Cause:** Schema cache or configuration issue

**Solution:**
1. Hard refresh browser: **Ctrl+F5** (or **Cmd+Shift+R** Mac)
2. Check `http://localhost:8000/api/schema/` directly (returns JSON schema)
3. Restart Django server
4. Check `settings.py` → `SPECTACULAR_SETTINGS` configuration

---

### **Issue: CORS Error (if frontend on different port)**

**Cause:** CORS not configured

**Status:** Already enabled in `settings.py`
- `CORS_ALLOW_ALL_ORIGINS = True` (development only)
- For production, set specific domains in `CORS_ALLOWED_ORIGINS`

---

## 📊 API Endpoints Reference

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|--------------|
| `/api/auth/token/` | POST | Get token | ❌ No |
| `/api/inventory/adjustments/` | GET | List data | ✅ Yes |
| `/api/inventory/adjustments/` | POST | Create | ✅ Yes |
| `/admin/` | GET/POST | Django admin | ✅ Yes (different auth) |
| `/api/docs/` | GET | Swagger UI | ❌ No |
| `/api/schema/` | GET | OpenAPI schema | ❌ No |

---

## 🚀 Next: Implement in Frontend

Once you've verified the endpoint works:

1. See **AUTH_QUICK_START.md** for minimal examples
2. See **FRONTEND_AUTH_GUIDE.md** for complete framework examples
3. Choose your implementation (React, Vue, Vanilla JS, etc.)
4. Copy the appropriate code
5. Test with Postman first before frontend implementation

---

## 📞 Quick Reference: Common Commands

```bash
# Start server
python manage.py runserver

# View open API docs
# http://localhost:8000/api/docs/

# Test endpoint
python test_auth.py

# Create admin user if needed
python manage.py createsuperuser

# Check URLs
python manage.py show_urls | grep -i auth

# View database
python manage.py dbshell

# View Django logs
tail -f logs/django.log  # if you have logging configured
```
