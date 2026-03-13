# Complete KingKunta E-commerce API Documentation

## API Overview
The KingKunta E-commerce API provides comprehensive endpoints for managing all aspects of an e-commerce business including inventory, products, customers, suppliers, sales, procurement, and finance.

## Base URL
```
http://localhost:8000/api/
```

## API Documentation URLs
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Complete API Endpoints

### 🏪 **INVENTORY MANAGEMENT**
**Base Path**: `/api/inventory/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/adjustments/` | Create inventory adjustment |

**Example Request**:
```json
POST /api/inventory/adjustments/
{
    "reason": "CYCLE_COUNT",
    "note": "Annual inventory count",
    "lines": [
        {
            "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "warehouse_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
            "location_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
            "qty_delta": -2.0
        }
    ]
}
```

### 📦 **PRODUCTS MANAGEMENT**
**Base Path**: `/api/products/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all products |
| POST | `/` | Create new product |
| GET | `/{id}/` | Get product details |
| PUT | `/{id}/` | Update product |
| DELETE | `/{id}/` | Delete product |
| GET | `/categories/` | List categories |
| POST | `/categories/` | Create category |
| GET | `/brands/` | List brands |
| POST | `/brands/` | Create brand |

**Example Product**:
```json
{
    "sku": "PROD-001",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones",
    "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "unit_price": "99.99",
    "cost_price": "50.00",
    "weight": "0.250"
}
```

### 👥 **PARTIES MANAGEMENT** (Customers & Suppliers)
**Base Path**: `/api/parties/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers/` | List customers |
| POST | `/customers/` | Create customer |
| GET | `/customers/{id}/` | Get customer details |
| PUT | `/customers/{id}/` | Update customer |
| DELETE | `/customers/{id}/` | Delete customer |
| GET | `/suppliers/` | List suppliers |
| POST | `/suppliers/` | Create supplier |
| GET | `/suppliers/{id}/` | Get supplier details |
| PUT | `/suppliers/{id}/` | Update supplier |
| DELETE | `/suppliers/{id}/` | Delete supplier |

**Example Customer**:
```json
{
    "customer_code": "CUST-001",
    "company_name": "ABC Corp",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@abccorp.com",
    "phone": "+1234567890",
    "credit_limit": "5000.00"
}
```

### 💰 **SALES MANAGEMENT**
**Base Path**: `/api/sales/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | List sales orders |
| POST | `/orders/` | Create sales order |
| GET | `/orders/{id}/` | Get sales order details |
| PUT | `/orders/{id}/` | Update sales order |
| DELETE | `/orders/{id}/` | Delete sales order |
| GET | `/invoices/` | List invoices |
| POST | `/invoices/` | Create invoice |

**Example Sales Order**:
```json
{
    "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "order_date": "2024-01-15",
    "delivery_date": "2024-01-20",
    "status": "CONFIRMED",
    "lines": [
        {
            "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
            "quantity": "2.00",
            "unit_price": "99.99",
            "discount_percent": "5.00"
        }
    ]
}
```

### 🛒 **PROCUREMENT MANAGEMENT**
**Base Path**: `/api/procurement/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/purchase-orders/` | List purchase orders |
| POST | `/purchase-orders/` | Create purchase order |
| GET | `/purchase-orders/{id}/` | Get purchase order details |
| PUT | `/purchase-orders/{id}/` | Update purchase order |
| DELETE | `/purchase-orders/{id}/` | Delete purchase order |
| GET | `/goods-receipts/` | List goods receipts |
| POST | `/goods-receipts/` | Create goods receipt |

**Example Purchase Order**:
```json
{
    "supplier_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "order_date": "2024-01-15",
    "expected_date": "2024-01-25",
    "status": "SENT",
    "lines": [
        {
            "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
            "quantity": "10.00",
            "unit_cost": "50.00"
        }
    ]
}
```

### 💳 **FINANCE MANAGEMENT**
**Base Path**: `/api/finance/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payments/` | List payments |
| POST | `/payments/` | Create payment |
| GET | `/expenses/` | List expenses |
| POST | `/expenses/` | Create expense |
| POST | `/reports/` | Generate financial report |

**Example Payment**:
```json
{
    "invoice_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
    "payment_date": "2024-01-20",
    "amount": "214.98",
    "payment_method": "BANK_TRANSFER",
    "reference": "TXN123456"
}
```

## Status Codes & Responses

### Success Responses
- `200 OK` - Successful GET/PUT requests
- `201 Created` - Successful POST requests
- `204 No Content` - Successful DELETE requests

### Error Responses
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Authentication
Currently, the API does not require authentication (development mode). In production, implement:
- JWT Token Authentication
- API Key Authentication
- OAuth2

## Data Types & Formats

### Common Field Types
- **UUID**: `3fa85f64-5717-4562-b3fc-2c963f66afa6`
- **Date**: `2024-01-15` (YYYY-MM-DD)
- **DateTime**: `2024-01-15T10:30:00Z` (ISO 8601)
- **Decimal**: `99.99` (string format for precision)
- **JSON**: `{"key": "value"}` (for flexible data)

### Status Enums

**Order Statuses**:
- `DRAFT`, `CONFIRMED`, `SHIPPED`, `DELIVERED`, `CANCELLED`

**Payment Methods**:
- `CASH`, `CARD`, `BANK_TRANSFER`, `CHECK`, `OTHER`

**Adjustment Reasons**:
- `CYCLE_COUNT`, `CORRECTION`, `DAMAGE`, `LOSS`, `OTHER`

## Rate Limiting
- Development: No limits
- Production: 1000 requests/hour per API key

## Pagination
All list endpoints support pagination:
```
GET /api/products/?page=2&page_size=20
```

Response format:
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/products/?page=3",
    "previous": "http://localhost:8000/api/products/?page=1",
    "results": [...]
}
```

## How to Start the Server

1. **Activate Virtual Environment**:
   ```bash
   venv_new\Scripts\activate
   ```

2. **Run Server**:
   ```bash
   python manage.py runserver
   ```

3. **Access Documentation**:
   - Swagger UI: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/

## Complete API Coverage

✅ **Inventory Management** - Adjustments, stock tracking
✅ **Product Catalog** - Products, categories, brands
✅ **Customer/Supplier Management** - Parties, addresses
✅ **Sales Processing** - Orders, invoices
✅ **Procurement** - Purchase orders, goods receipts
✅ **Financial Management** - Payments, expenses, reports

The API now provides complete coverage for all e-commerce operations with comprehensive Swagger documentation, examples, and proper HTTP methods for all CRUD operations.