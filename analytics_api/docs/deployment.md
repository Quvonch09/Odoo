# Production Deployment Guide

## Architecture

- `FastAPI + SQLAlchemy async` analytics API
- `PostgreSQL 18` Odoo database
- `analytics` schema for API auth and audit tables
- `Redis` for cache and rate limit backend
- `Nginx` reverse proxy
- `Gunicorn + UvicornWorker` app runtime
- `Prometheus metrics` on `/metrics`

## Folder Structure

```text
analytics_api/
├── app/
├── alembic/
├── docker/
├── docs/
├── scripts/
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## PostgreSQL Permissions

Use a dedicated application user:

```sql
CREATE USER analytics_app WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE odoo TO analytics_app;
GRANT USAGE ON SCHEMA public TO analytics_app;
GRANT SELECT ON TABLE
    res_partner,
    sale_order,
    sale_order_line,
    account_move,
    account_move_line,
    crm_lead,
    product_template,
    product_product,
    res_users,
    hr_employee
TO analytics_app;

CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION analytics_app;
GRANT USAGE, CREATE ON SCHEMA analytics TO analytics_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO analytics_app;
```

## Startup

```bash
cp .env.example .env
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
```

## Ubuntu 24.04 Server Setup

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx fail2ban
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

## SSL Setup

If you terminate TLS on host nginx:

```bash
sudo certbot --nginx -d api.example.com
```

If you terminate TLS in containerized nginx, mount:

- `/etc/letsencrypt/live/api.example.com/fullchain.pem`
- `/etc/letsencrypt/live/api.example.com/privkey.pem`

## systemd Service

`/etc/systemd/system/odoo-analytics-api.service`

```ini
[Unit]
Description=Odoo Analytics API
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/opt/analytics_api
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

## Gunicorn/Uvicorn

Default container command:

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

Tune workers as:

- `workers = (2 x CPU) + 1`
- Keep `--timeout 120` for heavy aggregation queries

## Backup Strategy

- Daily PostgreSQL logical dump for `analytics` schema
- Physical base backup or WAL archiving for full Odoo DB
- Daily Redis snapshot is optional; cache can be rebuilt
- Keep encrypted offsite backups for 30-90 days

Example:

```bash
pg_dump -h localhost -U postgres -d odoo -n analytics -Fc -f /backup/analytics_$(date +%F).dump
pg_dump -h localhost -U postgres -d odoo -Fc -f /backup/odoo_full_$(date +%F).dump
```

## Security Recommendations

- Put API behind private network or VPN when possible
- Restrict `CORS_ORIGINS` to exact BI domains
- Use long random `SECRET_KEY`
- Rotate API keys every 90 days
- Enable `fail2ban` for nginx logs
- Apply host firewall: allow only `80/443/22`
- Disable direct PostgreSQL access from analyst networks
- Use read-only DB grants on Odoo tables

## Looker Studio Integration

Looker Studio does not connect to arbitrary REST APIs directly without connector tooling. Recommended options:

1. Use a community REST connector and point it to:
   - `GET https://api.example.com/api/v1/dashboard`
   - `GET https://api.example.com/api/v1/orders`
   - `GET https://api.example.com/api/v1/invoices`
2. Send API Key in header:
   - `X-API-Key: ak_xxx`
3. If connector does not support headers, use JWT login first or deploy a small Looker Studio Community Connector proxy.

For Power BI or Tableau, use native web connector with:

- Base URL: `https://api.example.com/api/v1/orders?page=1&size=100`
- Header: `X-API-Key: ak_xxx`

## Example Requests

### Login

```bash
curl -X POST https://api.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"ChangeMe123!"}'
```

### Customers

```bash
curl -X GET "https://api.example.com/api/v1/customers?page=1&size=20&search=acme" \
  -H "Authorization: Bearer <jwt>"
```

### Dashboard

```bash
curl -X GET "https://api.example.com/api/v1/dashboard?year=2026&month=5" \
  -H "X-API-Key: ak_xxx"
```
