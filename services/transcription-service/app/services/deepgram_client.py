import logging
import httpx
import json
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepgramClient:
    """Client để interact với Deepgram API"""
    
    BASE_URL = "https://api.deepgram.com/v1"
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def transcribe_url(
        self,
        signed_url: str,
        request_id: str,
        model: str = "nova-2",
        options: Optional[dict] = None,
    ) -> dict:
        """
        Gọi Deepgram API để transcribe URL
        
        Args:
            signed_url: Signed URL của file từ Supabase Storage
            request_id: UUID của job để Deepgram track
            model: Deepgram model (nova-2, nova-1, etc)
            options: Tùy chọn như {diarize: true, punctuate: true, language: "vi"}
        
        Returns:
            {
                "request_id": "...",
                "status": "pending|success|error"
            }
        """
        try:
            # Build query parameters
            params = {
                "model": model,
                "callback": f"{self._get_webhook_url()}",  # Deepgram sẽ gọi webhook này
                "callback_method": "post",
            }
            
            # Add options
            if options:
                if options.get("diarize"):
                    params["diarize"] = "true"
                if options.get("punctuate"):
                    params["punctuate"] = "true"
                if options.get("language"):
                    params["language"] = options["language"]
                if options.get("smart_format"):
                    params["smart_format"] = "true"
            
            # Request body
            payload = {
                "url": signed_url,
                "metadata": {
                    "request_id": request_id,  # Store our job ID so webhook can find it
                }
            }
            
            logger.info(
                f"Calling Deepgram API with request_id={request_id}, "
                f"url={signed_url[:50]}..., model={model}"
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/listen",
                    headers=self.headers,
                    json=payload,
                    params=params,
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Deepgram response: {result}")
                
                return {
                    "request_id": result.get("request_id", request_id),
                    "status": "pending",
                    "dg_request_id": result.get("request_id"),
                }
        
        except httpx.HTTPError as e:
            logger.error(f"Deepgram API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Deepgram: {e}")
            raise
    
    def _get_webhook_url(self) -> str:
        """
        Lấy webhook URL từ config
        """
        return settings.WEBHOOK_URL
