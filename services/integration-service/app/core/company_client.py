import httpx
from app.core.config import settings


async def get_company_trello_credentials(company_id: str) -> dict:
    """Lấy trello_api_key, trello_token từ Company Service."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.COMPANY_SERVICE_URL}/companies/{company_id}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "trello_api_key": data.get("trello_api_key"),
            "trello_token": data.get("trello_token"),
        }


async def get_trello_member_id(company_id: str, user_id: str) -> str | None:
    """Lấy trello_member_id của user từ Company Service."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.COMPANY_SERVICE_URL}/companies/{company_id}/members/{user_id}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("trello_member_id")
        except Exception:
            return None
