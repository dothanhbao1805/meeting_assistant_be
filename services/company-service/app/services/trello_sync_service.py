"""
Trello API service for syncing boards
"""
import httpx
from fastapi import HTTPException, status


async def fetch_trello_boards(api_key: str, token: str) -> list[dict]:
    """
    Fetch all boards from Trello using API key and token
    
    Returns: List of boards with id, name, and url
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get member's boards
            response = await client.get(
                "https://api.trello.com/1/members/me/boards",
                params={
                    "key": api_key,
                    "token": token,
                    "fields": "id,name,url"
                },
                timeout=10.0
            )
            response.raise_for_status()
            
            boards = response.json()
            return [
                {
                    "id": board["id"],
                    "name": board["name"],
                    "url": board["url"]
                }
                for board in boards
            ]
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Trello API key or token: {e.response.text}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Trello API timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch Trello boards: {str(e)}"
        )
