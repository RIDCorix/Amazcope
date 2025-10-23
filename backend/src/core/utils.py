import json
import uuid
from datetime import datetime
from typing import Any

from core.config import settings


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        """Override default JSON encoding for UUID objects."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def now() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(tz=settings.TIMEZONE)


def trans_error_message(error: Exception) -> str:
    err_module = type(error).__module__
    err_type = type(error).__name__
    err_content = str(error)
    return f"{err_module}.{err_type}: {err_content}"


def dump_json(data: dict) -> str:
    """Serialize a dictionary to a JSON string using the custom UUID encoder."""
    return json.dumps(data, cls=UUIDEncoder)
