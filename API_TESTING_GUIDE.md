# Guide de Test des API Endpoints - KingKunta E-commerce

## Ordre de Test Recommandé

### 1. AUTHENTICATION
**POST** `/api/auth/token/`
```json
{
    "username": "admin",
    "password": "your_password"
}
```

### 2. PRODUCTS MODULE

#### 2.1 Créer une Catégorie
**POST** `/api/products/categories/`
```json
{
    "name": "Electronics",
    "is_active": true
}
```

#### 2.2 Créer une Marque
**POST** `/api/products/brands/`
```json
{
    "name": "Samsung",
    "description": "Electronics brand",
    "is_active": true
}
```

#### 2.3 Créer un Produit
**POST** `/api/products/`
```json
{
    "sku": "PROD-001",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones",
    "category_id": "CATEGORY_ID_FROM_STEP_2.1",
    "brand_id": "BRAND_ID_FROM_STEP_2.2",
    "unit_price": "99.99",
    "cost_price": "50.00",
    "weight": "0.250",
    "dimensions": {"length": 20, "width": 15, "height": 8}
}
```

#### 2.4 Lister les Produits
**GET** `/api/products/`

#### 2.5 Lister les Catégories
**GET** `/api/products/categories/`

#### 2.6 Lister les Marques
**GET** `/api/products/brands/`

### 3. PARTIES MODULE

#### 3.1 Créer un Client
**POST** `/api/parties/customers/`
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

#### 3.2 Créer un Fournisseur
**POST** `/api/parties/suppliers/`
```json
{
    "supplier_code": "SUPP-001",
    "company_name": "Tech Supplies Ltd",
    "contact_person": "Jane Smith",
    "email": "jane@techsupplies.com",
    "phone": "+1987654321",
    "payment_terms": "Net 30"
}
```

#### 3.3 Lister les Clients
**GET** `/api/parties/customers/`

#### 3.4 Lister les Fournisseurs
**GET** `/api/parties/suppliers/`

### 4. SALES MODULE

#### 4.1 Créer une Commande de Vente
**POST** `/api/sales/orders/`
```json
{
    "customer_id": "CUSTOMER_ID_FROM_STEP_3.1",
    "order_date": "2024-01-15",
    "delivery_date": "2024-01-20",
    "tax_amount": "15.00",
    "notes": "Rush order",
    "lines": [
        {
            "product_id": "PRODUCT_ID_FROM_STEP_2.3",
            "quantity": "2.00",
            "unit_price": "99.99",
            "discount_percent": "5.00"
        }
    ]
}
```

#### 4.2 Créer une Facture
**POST** `/api/sales/invoices/`
```json
{
    "sales_order_id": "SALES_ORDER_ID_FROM_STEP_4.1",
    "customer_id": "CUSTOMER_ID_FROM_STEP_3.1",
    "invoice_date": "2024-01-15",
    "due_date": "2024-02-15",
    "subtotal": "199.98",
    "tax_amount": "15.00",
    "total_amount": "214.98"
}
```

#### 4.3 Lister les Commandes de Vente
**GET** `/api/sales/orders/`

#### 4.4 Lister les Factures
**GET** `/api/sales/invoices/`

### 5. PROCUREMENT MODULE

#### 5.1 Créer un Bon de Commande
**POST** `/api/procurement/purchase-orders/`
```json
{
    "supplier_id": "SUPPLIER_ID_FROM_STEP_3.2",
    "order_date": "2024-01-15",
    "expected_date": "2024-01-25",
    "tax_amount": "20.00",
    "notes": "Urgent order",
    "lines": [
        {
            "product_id": "PRODUCT_ID_FROM_STEP_2.3",
            "quantity": "10.00",
            "unit_cost": "50.00"
        }
    ]
}
```

#### 5.2 Créer une Réception de Marchandises
**POST** `/api/procurement/goods-receipts/`
```json
{
    "purchase_order_id": "PURCHASE_ORDER_ID_FROM_STEP_5.1",
    "supplier_id": "SUPPLIER_ID_FROM_STEP_3.2",
    "receipt_date": "2024-01-25",
    "warehouse_id": "WAREHOUSE_ID_NEEDED",
    "notes": "All items received in good condition"
}
```

#### 5.3 Lister les Bons de Commande
**GET** `/api/procurement/purchase-orders/`

#### 5.4 Lister les Réceptions
**GET** `/api/procurement/goods-receipts/`

### 6. FINANCE MODULE

#### 6.1 Créer un Paiement
**POST** `/api/finance/payments/`
```json
{
    "invoice_id": "INVOICE_ID_FROM_STEP_4.2",
    "customer_id": "CUSTOMER_ID_FROM_STEP_3.1",
    "payment_date": "2024-01-20",
    "amount": "214.98",
    "payment_method": "BANK_TRANSFER",
    "reference": "TXN123456",
    "notes": "Payment for invoice INV-001"
}
```

#### 6.2 Créer une Dépense
**POST** `/api/finance/expenses/`
```json
{
    "category": "OFFICE",
    "description": "Office supplies - printer paper",
    "amount": "45.99",
    "expense_date": "2024-01-15",
    "supplier_id": "SUPPLIER_ID_FROM_STEP_3.2"
}
```

#### 6.3 Générer un Rapport Financier
**POST** `/api/finance/reports/`
```json
{
    "report_type": "SALES_SUMMARY",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

#### 6.4 Lister les Paiements
**GET** `/api/finance/payments/`

#### 6.5 Lister les Dépenses
**GET** `/api/finance/expenses/`

### 7. INVENTORY MODULE

#### 7.1 Créer un Ajustement d'Inventaire
**POST** `/api/inventory/adjustments/`
```json
{
    "reason": "CYCLE_COUNT",
    "note": "Annual inventory count - variance adjustments",
    "lines": [
        {
            "product_id": "PRODUCT_ID_FROM_STEP_2.3",
            "warehouse_id": "WAREHOUSE_ID_NEEDED",
            "location_id": null,
            "batch_code": null,
            "expires_on": null,
            "qty_delta": -2.0
        }
    ]
}
```

## Notes Importantes

1. **Remplacez les IDs** : Utilisez les vrais IDs retournés par chaque étape
2. **Ordre obligatoire** : Respectez l'ordre pour éviter les erreurs de dépendances
3. **Authentication** : Utilisez le token retourné dans l'en-tête `Authorization: Token YOUR_TOKEN`
4. **Warehouse ID** : Vous devrez créer un entrepôt via l'admin Django ou ajouter un endpoint

## Statuts de Réponse Attendus

- **200 OK** : GET réussi
- **201 Created** : POST réussi
- **400 Bad Request** : Données invalides
- **401 Unauthorized** : Token manquant/invalide
- **404 Not Found** : Ressource non trouvée

## Accès Swagger UI

Testez directement via : `http://localhost:8000/api/docs/`