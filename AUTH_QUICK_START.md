# Quick Implementation Guide: Bearer Token Authentication

## ⚡ 30-Second Overview

Your API uses **Bearer Token Authentication**:
1. User sends username/password → Backend returns a **token**
2. User includes that token in every API request
3. Backend validates the token and returns data

---

## 🔗 How to Find the Endpoint

**Endpoint URL:** `http://localhost:8000/api/auth/token/`

**Visual Navigation:**
```
Your Django Server
├── http://localhost:8000/admin/              ← Django admin
├── http://localhost:8000/api/                ← API root
├── http://localhost:8000/api/docs/           ← Swagger documentation
│   └── Look for "Authentication" section
│       └── You should see POST /api/auth/token/
├── http://localhost:8000/api/auth/token/     ← Token endpoint (YOU ARE HERE)
└── http://localhost:8000/api/inventory/...   ← Other API endpoints
```

---

## 🔐 Step-by-Step: How to Use

### **STEP 1: Login (Get Token)**

**Using Postman:**
1. Create a new request
2. Set to **POST**
3. URL: `http://localhost:8000/api/auth/token/`
4. Go to **Body** tab → select **raw** → **JSON**
5. Paste:
   ```json
   {
     "username": "admin",
     "password": "password123"
   }
   ```
6. Click **Send**

**Response Example:**
```json
{
    "token": "3c0c0fe4d8e8b7a75a4f2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f",
    "user_id": 1,
    "email": "admin@example.com"
}
```

**⚠️ Copy that long `token` value!**

---

### **STEP 2: Use Token in Next Request**

**Using Postman:**
1. Create another request (e.g., GET `/api/inventory/adjustments/`)
2. Go to **Headers** tab
3. Add new header:
   - **Key:** `Authorization`
   - **Value:** `Bearer 3c0c0fe4d8e8b7a75a4f2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f`
   
   *(Replace with YOUR token from Step 1)*

4. Click **Send** → You should get data!

---

## 🧪 Quick Test

**Run automated tests:**

```bash
# Test with Python (recommended)
cd /home/santos/Documents/KingKuntaEcommerce
python test_auth.py

# Or test with bash script
bash test_auth_endpoint.sh
```

---

## 💻 Frontend Implementation (Minimal Example)

### **HTML + Vanilla JavaScript:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>E-commerce Login</title>
</head>
<body>
    <h1>E-commerce API Login</h1>

    <!-- LOGIN FORM -->
    <h2>1. Login</h2>
    <form id="loginForm">
        <input type="text" id="username" placeholder="Username" value="admin" />
        <input type="password" id="password" placeholder="Password" value="password123" />
        <button type="submit">Login & Get Token</button>
    </form>
    <p id="loginResult"></p>

    <!-- API CALL FORM -->
    <h2>2. Make API Call</h2>
    <button id="apiBut">Fetch Inventory (using token)</button>
    <pre id="apiResult"></pre>

    <script>
        // ====== AUTHENTICATION LOGIC ======
        
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                // STEP 1: Send username/password, get token back
                const response = await fetch('http://localhost:8000/api/auth/token/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (!response.ok) throw new Error('Login failed');

                const data = await response.json();
                const token = data.token;

                // STEP 2: Save token to browser storage
                localStorage.setItem('auth_token', token);

                document.getElementById('loginResult').innerHTML = `
                    <strong style="color: green;">✓ Login successful!</strong><br/>
                    Token: ${token.substring(0, 50)}...<br/>
                    (Saved to browser storage)
                `;

            } catch (error) {
                document.getElementById('loginResult').innerHTML = 
                    `<strong style="color: red;">❌ Login failed: ${error.message}</strong>`;
            }
        });

        // ====== API CALL WITH TOKEN ======
        document.getElementById('apiButton').addEventListener('click', async () => {
            const token = localStorage.getItem('auth_token');

            if (!token) {
                alert('Please login first!');
                return;
            }

            try {
                // STEP 3: Make API call with Bearer token
                const response = await fetch('http://localhost:8000/api/inventory/adjustments/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`  // ← Token goes here!
                    }
                });

                if (response.status === 401) {
                    document.getElementById('apiResult').textContent = 
                        'Token expired. Please login again.';
                    localStorage.removeItem('auth_token');
                    return;
                }

                if (!response.ok) throw new Error('API call failed');

                const data = await response.json();
                document.getElementById('apiResult').textContent = JSON.stringify(data, null, 2);

            } catch (error) {
                document.getElementById('apiResult').textContent = 
                    `Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
```

---

## 📱 React Hook Implementation:

```jsx
import { useState, useCallback } from 'react';

export function useAuth() {
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  // LOGIN: Get token with username/password
  const login = useCallback(async (username, password) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) throw new Error('Invalid credentials');

      const data = await response.json();
      localStorage.setItem('auth_token', data.token);
      setToken(data.token);
      setUser({ user_id: data.user_id, email: data.email });
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  // API CALL: Make requests with token automatically included
  const request = useCallback(async (endpoint) => {
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`http://localhost:8000/api${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`  // ← Token included here
      }
    });

    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      setToken(null);
      throw new Error('Session expired');
    }

    if (!response.ok) throw new Error('API failed');
    return response.json();
  }, [token]);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  }, []);

  return { token, user, error, login, request, logout };
}

// USAGE:
function App() {
  const { token, user, login, request, logout } = useAuth();

  if (!token) {
    return <LoginPage onLogin={login} />;
  }

  return <DashboardPage user={user} request={request} onLogout={logout} />;
}
```

---

## 🐍 Python/Requests Implementation:

```python
import requests

API_BASE = "http://localhost:8000/api"

# STEP 1: Login
response = requests.post(
    f"{API_BASE}/auth/token/",
    json={"username": "admin", "password": "password123"}
)
token = response.json()['token']
print(f"Token: {token}")

# STEP 2: Use token in subsequent requests
headers = {'Authorization': f'Bearer {token}'}
data = requests.get(f"{API_BASE}/inventory/adjustments/", headers=headers).json()
print(data)
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"POST /api/auth/token/ not found"** | Run `python manage.py runserver` first |
| **"Invalid credentials"** | Username/password wrong. Default is admin/password123 |
| **"Endpoint missing in Swagger"** | Refresh browser cache or go to http://localhost:8000/api/schema/ |
| **401 on API call with token** | Token expired or invalid format. Re-login. |
| **Getting 500 error** | Check Django console for errors |

---

## ✅ Checklist for Frontend Implementation

- [ ] Backend running: `python manage.py runserver`
- [ ] Can POST to `/api/auth/token/` and get token
- [ ] Token saved to `localStorage` or session storage
- [ ] Token included in `Authorization: Bearer <token>` header
- [ ] API calls return 200 OK (not 401)
- [ ] On 401 response, user is redirected to login
- [ ] Token is cleared on logout

---

## 📚 Full Documentation

See **`FRONTEND_AUTH_GUIDE.md`** for complete examples in:
- Vanilla JavaScript
- React hooks
- Vue.js
- Angular
- Axios
- And more!
