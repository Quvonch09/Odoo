# Odoo 19 Analytics API

Production-ready `read-only` analytics API for Odoo 19 and PostgreSQL 18.

## Features

- FastAPI async backend
- SQLAlchemy 2.0 async
- PostgreSQL connection pooling
- Redis cache
- JWT and API key authentication
- RBAC: `ADMIN`, `ANALYST`, `READ_ONLY`
- Pagination, filtering, sorting, search
- Structured logging
- Prometheus metrics
- Nginx reverse proxy
- Alembic migrations for auth/audit schema

## Run

```bash
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Detailed deployment guide: [docs/deployment.md](/C:/odoo-19/analytics_api/docs/deployment.md)
