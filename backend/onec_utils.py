"""Общие утилиты для работы с 1С OData API."""
from config import settings


def odata_url(entity: str) -> str:
    """Строит URL до OData-сущности 1С."""
    base = (settings.ONEC_API_URL or "").rstrip("/")
    return f"{base}/odata/standard.odata/{entity}"


def odata_auth() -> tuple[str, str]:
    return (settings.ONEC_USERNAME or "", settings.ONEC_PASSWORD or "")
