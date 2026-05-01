import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.webhook import DeepgramWebhookPayload, WebhookResponse
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def get_webhook_service(db: AsyncSession = Depends(get_db)) -> WebhookService:
    return WebhookService(db)


@router.post("/deepgram", response_model=WebhookResponse)
async def deepgram_webhook(
    request: Request,
    service: WebhookService = Depends(get_webhook_service),
):

    try:
        body = await request.body()

        if WebhookService.requires_basic_auth_verification():
            authorization = request.headers.get("Authorization")
            if not authorization:
                logger.error("Missing Authorization header for Deepgram webhook")
                raise HTTPException(status_code=401, detail="Missing basic auth")

            if not WebhookService.verify_basic_auth(authorization):
                logger.error("Invalid Authorization header for Deepgram webhook")
                raise HTTPException(status_code=401, detail="Invalid basic auth")
        elif WebhookService.requires_dg_token_verification():
            dg_token = request.headers.get("dg-token")
            if not dg_token:
                logger.error("Missing dg-token header")
                raise HTTPException(status_code=401, detail="Missing dg-token")

            if not WebhookService.verify_dg_token(dg_token):
                logger.error("Invalid dg-token header")
                raise HTTPException(status_code=401, detail="Invalid dg-token")
        elif WebhookService.requires_signature_verification():
            signature = request.headers.get("X-DG-Signature")
            if not signature:
                logger.error("Missing X-DG-Signature header")
                raise HTTPException(status_code=401, detail="Missing signature")

            if not WebhookService.verify_signature(body, signature):
                logger.error("Invalid X-DG-Signature header")
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning(
                "Skipping Deepgram webhook authentication because no "
                "dg-token, Basic Auth, or legacy signature config is set"
            )

        payload_dict = json.loads(body)
        payload = DeepgramWebhookPayload(**payload_dict)

        result = await service.process_webhook(payload)
        logger.info(f"Webhook processed successfully: {result}")

        return WebhookResponse(received=True)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
