# Frontend Authentication Guide - Bearer Token Implementation

## Overview

Your Django backend uses **Bearer Token Authentication**. Here's how to implement this in your frontend.

---

## Part 1: Understanding the Flow

```
┌─────────────┐                      ┌──────────────────┐
│   Frontend  │                      │  Django Backend  │
└─────────────┘                      └──────────────────┘
      │                                       │
      │ POST /api/auth/token/                 │
      │ {username, password}                  │
      ├────────────────────────────────────>  │
      │                                       │
      │                                       │ Generate & store token
      │                                       │
      │ Response: {token, user_id, email}     │
      │ <───────────────────────────────────  │
      │                                       │
      │ Save token to localStorage            │
      │                                       │
      │ GET /api/inventory/                   │
      │ Header: Authorization: Bearer TOKEN   │
      ├────────────────────────────────────>  │
      │                                       │
      │                                       │ Validate token
      │ Response: data                        │
      │ <───────────────────────────────────  │
```

---

## Part 2: Backend Endpoint Details

### 1. **Login (Get Token)**

**Endpoint:** `POST /api/auth/token/`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
```

**Response (200 OK):**
```json
{
    "token": "3c0c0fe4d8e8b7a75a4f2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f",
    "user_id": 1,
    "email": "admin@example.com"
}
```

### 2. **Use Token in API Requests**

**For any subsequent API call**, include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/inventory/adjustments/ \
  -H "Authorization: Bearer 3c0c0fe4d8e8b7a75a4f2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f"
```

---

## Part 3: Frontend Implementation Examples

### **Option A: Vanilla JavaScript (React/Vue/etc.)**

#### Step 1: Create an auth service
```javascript
// authService.js

class AuthService {
  constructor() {
    this.API_BASE = 'http://localhost:8000/api';
    this.TOKEN_KEY = 'auth_token';
    this.USER_KEY = 'auth_user';
  }

  /**
   * Login: Send username/password, get token back
   */
  async login(username, password) {
    try {
      const response = await fetch(`${this.API_BASE}/auth/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error(`Login failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Store token in localStorage
      localStorage.setItem(this.TOKEN_KEY, data.token);
      localStorage.setItem(this.USER_KEY, JSON.stringify({
        user_id: data.user_id,
        email: data.email,
      }));

      return {
        success: true,
        token: data.token,
        user: { user_id: data.user_id, email: data.email },
      };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Logout: Clear token from localStorage
   */
  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Get token from localStorage
   */
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Check if user is logged in
   */
  isLoggedIn() {
    return !!this.getToken();
  }

  /**
   * Make an authenticated API request (automatically adds Bearer token)
   */
  async request(endpoint, options = {}) {
    const token = this.getToken();
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add Bearer token to Authorization header
    headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${this.API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired or invalid
      this.logout();
      throw new Error('Session expired. Please login again.');
    }

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get current user info from localStorage
   */
  getUser() {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }
}

// Export as singleton
export const authService = new AuthService();
```

#### Step 2: Use in your components

**Login Component:**
```javascript
// LoginComponent.js
import { authService } from './authService.js';

async function handleLogin(event) {
  event.preventDefault();
  
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  const result = await authService.login(username, password);

  if (result.success) {
    console.log('✓ Login successful!');
    console.log('Token:', result.token);
    console.log('User:', result.user);
    
    // Redirect to dashboard or app
    window.location.href = '/dashboard';
  } else {
    alert('Login failed: ' + result.error);
  }
}

// HTML
//  <form onsubmit="handleLogin(event)">
//    <input type="text" id="username" placeholder="Username" />
//    <input type="password" id="password" placeholder="Password" />
//    <button type="submit">Login</button>
//  </form>
```

**API Request Component:**
```javascript
// FetchDataComponent.js
import { authService } from './authService.js';

async function fetchInventory() {
  try {
    // This automatically includes the Bearer token
    const data = await authService.request('/inventory/adjustments/');
    console.log('Inventory data:', data);
    // Update UI with data
  } catch (error) {
    console.error('Error fetching inventory:', error);
  }
}

// Check if user is logged in before showing content
if (authService.isLoggedIn()) {
  fetchInventory();
} else {
  redirectToLogin();
}
```

---

### **Option B: React Hook (useAuth)**

```javascript
// useAuth.js
import { useState, useCallback } from 'react';

export function useAuth() {
  const [user, setUser] = useState(
    localStorage.getItem('auth_user') 
      ? JSON.parse(localStorage.getItem('auth_user')) 
      : null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) throw new Error('Invalid credentials');

      const data = await response.json();
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify({
        user_id: data.user_id,
        email: data.email,
      }));
      setUser({ user_id: data.user_id, email: data.email });
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
  }, []);

  const getToken = useCallback(() => {
    return localStorage.getItem('auth_token');
  }, []);

  const isLoggedIn = useCallback(() => {
    return !!localStorage.getItem('auth_token');
  }, []);

  const request = useCallback(async (endpoint, options = {}) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    const response = await fetch(`http://localhost:8000/api${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      logout();
      throw new Error('Session expired');
    }

    if (!response.ok) throw new Error('API request failed');
    return await response.json();
  }, [getToken, logout]);

  return {
    user,
    loading,
    error,
    login,
    logout,
    getToken,
    isLoggedIn,
    request,
  };
}
```

**Usage in React:**
```jsx
import { useAuth } from './useAuth';

function LoginPage() {
  const { login, loading, error } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(username, password);
    if (success) {
      window.location.href = '/dashboard';
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  );
}

function Dashboard() {
  const { user, request, logout } = useAuth();
  const [inventory, setInventory] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await request('/inventory/adjustments/');
        setInventory(data);
      } catch (err) {
        console.error('Failed to load inventory:', err);
      }
    }
    loadData();
  }, [request]);

  return (
    <div>
      <h1>Welcome, {user?.email}</h1>
      <button onClick={logout}>Logout</button>
      {/* Display inventory data */}
    </div>
  );
}
```

---

### **Option C: Axios (Common in Angular/Vue)**

```javascript
// axiosConfig.js
import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Interceptor: Add token to every request
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor: Handle 401 responses
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default API;
```

**Usage:**
```javascript
// Login
const login = async (username, password) => {
  const res = await API.post('/auth/token/', { username, password });
  localStorage.setItem('auth_token', res.data.token);
  return res.data;
};

// Get data (token is automatically included)
const getInventory = async () => {
  const res = await API.get('/inventory/adjustments/');
  return res.data;
};
```

---

## Part 4: Testing in Postman

1. **Step 1: Login and Get Token**
   - **URL:** `POST http://localhost:8000/api/auth/token/`
   - **Body (raw JSON):**
     ```json
     {
       "username": "admin",
       "password": "password123"
     }
     ```
   - **Click Send** → Copy the `token` value from the response

2. **Step 2: Use Token in Next Request**
   - **URL:** `GET http://localhost:8000/api/inventory/adjustments/`
   - **Headers tab** → Add:
     - **Key:** `Authorization`
     - **Value:** `Bearer <paste-your-token-here>`
   - **Click Send** → You should get the data back

---

## Part 5: Troubleshooting

| Issue | Solution |
|-------|----------|
| **401 Unauthorized** | Token is missing, invalid, or expired. Re-login |
| **Token not showing in Swagger UI** | Refresh the page; the schema is cached by the browser |
| **CORS errors** | CORS is already enabled in `settings.py` for development |
| **404 on /api/auth/token/** | Check that `core.urls` is included in main `urls.py` |
| **Username/password wrong** | Create a superuser: `python manage.py createsuperuser` |

---

## Part 6: Security Notes for Production

- ✅ Never store tokens in cookies without `HttpOnly` flag
- ✅ Use HTTPS only (not HTTP)
- ✅ Set `secure=True` and `sameSite='Strict'` for cookies if using them
- ✅ Rotate tokens periodically
- ✅ Disable CORS_ALLOW_ALL_ORIGINS and restrict to specific domains
- ✅ Use environment variables for API base URL

---

## Quick Reference

| Action | Code |
|--------|------|
| **Login** | `POST /api/auth/token/` with username/password |
| **Store Token** | Save response token to `localStorage` |
| **Make Requests** | Add header: `Authorization: Bearer <token>` |
| **Logout** | Clear token from `localStorage` |
| **Check Auth** | `if (localStorage.getItem('auth_token')) { ... }` |
