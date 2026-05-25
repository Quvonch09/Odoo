from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_response(
    message: str,
    data: Any,
    pagination: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": True,
        "message": message,
        "timestamp": _timestamp(),
        "data": data,
    }
    if pagination is not None:
        payload["pagination"] = pagination
    return payload


def error_response(message: str, errors: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "message": message,
        "timestamp": _timestamp(),
        "data": [],
    }
    if errors is not None:
        payload["errors"] = errors
    return payload
