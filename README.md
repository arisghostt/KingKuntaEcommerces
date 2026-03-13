# KingKunta E-commerce API

A Django REST Framework-based e-commerce API system for managing inventory, products, sales, and more.

## Project Structure

- **inventory** - Inventory management and adjustments
- **products** - Product catalog management (placeholder)
- **parties** - Customer/supplier management (placeholder)
- **procurement** - Purchase management (placeholder)
- **sales** - Sales management (placeholder)
- **finance** - Financial management (placeholder)
- **core** - Core functionality (placeholder)

## Features

### Implemented
- **Inventory Adjustments API**: Create inventory adjustments for cycle counts, corrections, damage, loss, etc.
- **API Documentation**: Swagger/OpenAPI documentation with drf-spectacular
- **Django Admin**: Built-in admin interface

### Planned
- Product management
- Customer/supplier management
- Sales processing
- Purchase orders
- Financial reporting

## Installation

1. **Activate Virtual Environment**:
   ```bash
   venv_new\Scripts\activate
   ```

2. **Install Dependencies** (already done):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema**: http://localhost:8000/api/schema/

### Inventory
- **POST /api/inventory/adjustments/** - Create inventory adjustment

### Example API Usage

**Create Inventory Adjustment**:
```json
POST /api/inventory/adjustments/
{
    "reason": "CYCLE_COUNT",
    "note": "Annual inventory count - variance adjustments",
    "lines": [
        {
            "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "warehouse_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
            "location_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
            "batch_code": null,
            "expires_on": null,
            "qty_delta": -2.0
        }
    ]
}
```

## Business Logic

### Inventory Adjustments
- **Positive qty_delta**: Increase stock
- **Negative qty_delta**: Decrease stock
- **Validation**: Cannot decrease stock below zero or reserved quantity
- **Audit Trail**: Full audit trail via InventoryTx records

## Technology Stack

- **Django 5.2.7** - Web framework
- **Django REST Framework 3.16.1** - API framework
- **drf-spectacular 0.29.0** - API documentation
- **psycopg2 2.9.11** - PostgreSQL adapter
- **Neon (PostgreSQL)** - Default database via `DATABASE_URL`

## Development Notes

- Database is configured for Neon PostgreSQL via `.env` (`DATABASE_URL`)
- Most apps are placeholder stubs - only inventory is implemented
- Models need to be created for actual database entities
- Business logic in services.py is placeholder implementation

## Next Steps

1. Define database models for all entities
2. Implement actual business logic in services
3. Add authentication and authorization
4. Implement remaining API endpoints
5. Add comprehensive tests
6. Set up production deployment configuration
