import asyncio

from app.services.auth_service import bootstrap_admin_user


if __name__ == "__main__":
    asyncio.run(bootstrap_admin_user())
