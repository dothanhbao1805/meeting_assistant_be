import httpx

from app.core.config import settings


def _company_service_url() -> str:
    return settings.COMPANY_SERVICE_URL.rstrip("/")


async def get_company_trello_credentials(company_id: str) -> dict:
    """Fetch Trello credentials from Company Service."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_company_service_url()}/companies/{company_id}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "trello_api_key": data.get("trello_api_key"),
            "trello_token": data.get("trello_token"),
        }


async def get_trello_member_id(company_id: str, user_id: str) -> str | None:
    """Fetch the Trello member id for a company member.

    Current project convention: task.resolved_user_id stores members.id.
    Company Service stores that Trello id in the member.trello_user_id field.
    The company_id argument is kept for the service contract, although the
    existing Company Service member lookup is by member id.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{_company_service_url()}/members/{user_id}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("trello_member_id") or data.get("trello_user_id")
        except Exception:
            return None
