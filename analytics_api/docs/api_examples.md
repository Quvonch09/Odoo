# API Examples

Base URL:

```text
https://api.example.com
```

Auth headers:

```text
Authorization: Bearer <jwt>
X-API-Key: ak_xxx
```

## 1. POST /auth/login

Request:

```json
{
  "email": "admin@example.com",
  "password": "ChangeMe123!"
}
```

Response:

```json
{
  "success": true,
  "message": "Login successful",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600,
    "role": "ADMIN"
  }
}
```

cURL:

```bash
curl -X POST "https://api.example.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"ChangeMe123!"}'
```

Postman:

```text
Method: POST
URL: https://api.example.com/auth/login
Body: raw JSON
```

## 2. GET /api/v1/customers

Request:

```text
/api/v1/customers?page=1&size=20&search=acme&country=US&sort_by=name&sort_order=asc
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 42,
      "name": "Acme LLC",
      "email": "finance@acme.com",
      "phone": "+1-555-1000",
      "city": "New York",
      "country_code": "US",
      "is_company": true,
      "active": true,
      "create_date": "2026-01-10T08:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 150
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/customers?page=1&size=20&search=acme" \
  -H "X-API-Key: ak_xxx"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/customers?page=1&size=20&search=acme
Headers: X-API-Key = ak_xxx
```

## 3. GET /api/v1/customers/{id}

Request:

```text
/api/v1/customers/42
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": {
    "id": 42,
    "name": "Acme LLC",
    "email": "finance@acme.com",
    "phone": "+1-555-1000",
    "city": "New York",
    "country_code": "US",
    "is_company": true,
    "active": true,
    "create_date": "2026-01-10T08:00:00Z",
    "customer_rank": 12,
    "total_invoices": 18,
    "total_orders": 27,
    "total_revenue": 94500.00
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/customers/42" \
  -H "Authorization: Bearer <jwt>"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/customers/42
Headers: Authorization = Bearer <jwt>
```

## 4. GET /api/v1/invoices

Request:

```text
/api/v1/invoices?page=1&size=20&payment_state=paid&date_from=2026-01-01&date_to=2026-12-31
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 1001,
      "name": "INV/2026/001",
      "partner_id": 42,
      "partner_name": "Acme LLC",
      "invoice_date": "2026-05-01",
      "invoice_date_due": "2026-05-15",
      "state": "posted",
      "payment_state": "paid",
      "amount_total": 1250.00,
      "amount_residual": 0.00
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 83
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/invoices?payment_state=paid" \
  -H "X-API-Key: ak_xxx"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/invoices?payment_state=paid
Headers: X-API-Key = ak_xxx
```

## 5. GET /api/v1/payments

Request:

```text
/api/v1/payments?page=1&size=20&date_from=2026-05-01&date_to=2026-05-31
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 501,
      "move_id": 1001,
      "partner_id": 42,
      "product_id": null,
      "payment_date": "2026-05-03",
      "debit": 0.00,
      "credit": 1250.00,
      "balance": -1250.00,
      "description": "Customer payment"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 90
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/payments?page=1&size=20" \
  -H "Authorization: Bearer <jwt>"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/payments?page=1&size=20
Headers: Authorization = Bearer <jwt>
```

## 6. GET /api/v1/leads

Request:

```text
/api/v1/leads?page=1&size=20&search=enterprise&sort_by=create_date&sort_order=desc
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 77,
      "name": "Enterprise rollout",
      "partner_name": "Beta Industries",
      "email_from": "cto@beta.com",
      "phone": "+1-555-2222",
      "user_id": 5,
      "expected_revenue": 45000.00,
      "probability": 60.00,
      "active": true,
      "create_date": "2026-05-11T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 45
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/leads?search=enterprise" \
  -H "X-API-Key: ak_xxx"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/leads?search=enterprise
Headers: X-API-Key = ak_xxx
```

## 7. GET /api/v1/products

Request:

```text
/api/v1/products?page=1&size=20&search=subscription&active=true
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 10,
      "template_id": 9,
      "name": "Enterprise Subscription",
      "default_code": "ENT-SUB",
      "active": true,
      "sale_ok": true,
      "type": "service",
      "list_price": 499.00
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 22
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/products?search=subscription" \
  -H "Authorization: Bearer <jwt>"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/products?search=subscription
Headers: Authorization = Bearer <jwt>
```

## 8. GET /api/v1/orders

Request:

```text
/api/v1/orders?page=1&size=20&state=sale&date_from=2026-01-01&date_to=2026-12-31
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": [
    {
      "id": 301,
      "name": "SO0301",
      "partner_id": 42,
      "partner_name": "Acme LLC",
      "user_id": 5,
      "state": "sale",
      "amount_total": 2400.00,
      "date_order": "2026-05-02T10:45:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 61
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/orders?state=sale" \
  -H "X-API-Key: ak_xxx"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/orders?state=sale
Headers: X-API-Key = ak_xxx
```

## 9. GET /api/v1/dashboard

Request:

```text
/api/v1/dashboard?year=2026&month=5
```

Response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "timestamp": "2026-05-25T10:30:00Z",
  "data": {
    "total_customers": 1800,
    "active_customers": 1640,
    "total_invoices": 5240,
    "paid_invoices": 4710,
    "unpaid_invoices": 530,
    "total_revenue": 8750000.00,
    "monthly_revenue": 745000.00,
    "yearly_revenue": 4200000.00,
    "total_leads": 620,
    "won_leads": 185,
    "lost_leads": 90,
    "conversion_rate": 29.84,
    "top_products": [
      {
        "id": 9,
        "name": "Enterprise Subscription",
        "qty": 400.00,
        "revenue": 199600.00
      }
    ],
    "top_customers": [
      {
        "id": 42,
        "name": "Acme LLC",
        "revenue": 94500.00
      }
    ],
    "employee_statistics": [
      {
        "id": 12,
        "name": "John Smith",
        "lead_count": 54,
        "won_count": 18
      }
    ]
  }
}
```

cURL:

```bash
curl -X GET "https://api.example.com/api/v1/dashboard?year=2026&month=5" \
  -H "X-API-Key: ak_xxx"
```

Postman:

```text
Method: GET
URL: https://api.example.com/api/v1/dashboard?year=2026&month=5
Headers: X-API-Key = ak_xxx
```
