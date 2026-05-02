import httpx
from typing import Optional

TRELLO_BASE = "https://api.trello.com/1"

PRIORITY_LABEL_COLORS = {
    "high": "red",
    "medium": "yellow",
    "low": "green",
}


class TrelloClient:
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key
        self.token = token

    def _auth(self) -> dict:
        return {"key": self.api_key, "token": self.token}

    async def get_or_create_label(
        self, board_id: str, name: str, color: str
    ) -> Optional[str]:
        """Lấy label theo tên, tạo mới nếu chưa có. Trả về label_id."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{TRELLO_BASE}/boards/{board_id}/labels",
                params=self._auth(),
            )
            resp.raise_for_status()
            labels = resp.json()

            for label in labels:
                if label.get("name") == name and label.get("color") == color:
                    return label["id"]

            # Tạo mới
            resp = await client.post(
                f"{TRELLO_BASE}/labels",
                params={
                    **self._auth(),
                    "name": name,
                    "color": color,
                    "idBoard": board_id,
                },
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def create_card(
        self,
        list_id: str,
        board_id: str,
        title: str,
        description: Optional[str],
        due_date: Optional[str],  # ISO format: "2026-05-10"
        member_id: Optional[str],
        priority: Optional[str],
    ) -> dict:
        """Tạo Trello card, trả về {"id": ..., "url": ...}"""
        params = {
            **self._auth(),
            "idList": list_id,
            "name": title,
            "desc": description or "",
        }

        if due_date:
            params["due"] = due_date

        if member_id:
            params["idMembers"] = member_id

        # Gắn label priority
        if priority and priority in PRIORITY_LABEL_COLORS:
            color = PRIORITY_LABEL_COLORS[priority]
            label_id = await self.get_or_create_label(
                board_id, priority.capitalize(), color
            )
            if label_id:
                params["idLabels"] = label_id

        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{TRELLO_BASE}/cards", params=params)
            resp.raise_for_status()
            data = resp.json()
            return {"id": data["id"], "url": data["shortUrl"]}
