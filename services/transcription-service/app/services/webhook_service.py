import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.repositories.job_repo import TranscriptionJobRepo
from app.repositories.transcript_repo import TranscriptRepo
from app.repositories.utterance_repo import UtteranceRepo
from app.schemas.webhook import DeepgramWebhookPayload

logger = logging.getLogger(__name__)

CHANNEL_TRANSCRIPTION_COMPLETED = "event:transcription.completed"


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = TranscriptionJobRepo(db)
        self.transcript_repo = TranscriptRepo(db)
        self.utterance_repo = UtteranceRepo(db)

    @staticmethod
    def requires_basic_auth_verification() -> bool:
        return bool(
            settings.DEEPGRAM_WEBHOOK_BASIC_USERNAME
            and settings.DEEPGRAM_WEBHOOK_BASIC_PASSWORD
        )

    @staticmethod
    def requires_dg_token_verification() -> bool:
        return bool(
            settings.DEEPGRAM_API_KEY_ID
            and settings.DEEPGRAM_API_KEY_ID.strip()
        )

    @staticmethod
    def requires_signature_verification() -> bool:
        return bool(
            settings.DEEPGRAM_WEBHOOK_SECRET
            and settings.DEEPGRAM_WEBHOOK_SECRET.strip()
        )

    @staticmethod
    def verify_basic_auth(authorization: str) -> bool:
        try:
            if not WebhookService.requires_basic_auth_verification():
                return False

            scheme, _, token = authorization.partition(" ")
            if scheme.lower() != "basic" or not token:
                return False

            decoded = base64.b64decode(token).decode("utf-8")
            username, _, password = decoded.partition(":")
            return (
                hmac.compare_digest(
                    username,
                    settings.DEEPGRAM_WEBHOOK_BASIC_USERNAME,
                )
                and hmac.compare_digest(
                    password,
                    settings.DEEPGRAM_WEBHOOK_BASIC_PASSWORD,
                )
            )
        except Exception as e:
            logger.error(f"Basic auth verification error: {e}")
            return False

    @staticmethod
    def verify_dg_token(dg_token: str) -> bool:
        try:
            if not WebhookService.requires_dg_token_verification():
                return False

            return hmac.compare_digest(
                settings.DEEPGRAM_API_KEY_ID.strip(),
                dg_token.strip(),
            )
        except Exception as e:
            logger.error(f"dg-token verification error: {e}")
            return False

    @staticmethod
    def verify_signature(payload: bytes, signature: str) -> bool:
        try:
            if not WebhookService.requires_signature_verification():
                return True

            expected_signature = hmac.new(
                settings.DEEPGRAM_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()

            scheme, _, provided_hex = signature.partition("=")
            if scheme != "sha256" or not provided_hex:
                return False

            return hmac.compare_digest(expected_signature, provided_hex)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    async def process_webhook(
        self,
        payload: DeepgramWebhookPayload,
    ) -> dict:
        try:
            request_id = payload.request_id
            logger.info(f"Processing webhook for request_id: {request_id}")

            job = await self._find_job_by_deepgram_id(request_id)
            if not job:
                logger.error(f"Job not found for request_id: {request_id}")
                raise ValueError(f"Job not found for request_id: {request_id}")

            if job.status == "done":
                logger.info(f"Job {job.id} already done, skipping")
                return {"received": True, "idempotent": True}

            transcript_data = self._parse_deepgram_response(payload)

            transcript = await self.transcript_repo.create(
                {
                    "job_id": str(job.id),
                    "meeting_id": str(job.meeting_id),
                    "full_text": transcript_data["full_text"],
                    "edited_text": None,
                    "is_edited": False,
                    "speaker_count": transcript_data["speaker_count"],
                    "confidence_avg": transcript_data["confidence_avg"],
                    "language_detected": (
                        payload.result.channels[0].detected_language
                        if payload.result.channels
                        else None
                    ),
                    "raw_deepgram_response": payload.model_dump(),
                }
            )

            utterances_data = transcript_data["utterances"]
            created_utterances = await self.utterance_repo.create_batch(
                [
                    {
                        "transcript_id": str(transcript.id),
                        "speaker_label": u["speaker_label"],
                        "text": u["text"],
                        "start_time_ms": u["start_time_ms"],
                        "end_time_ms": u["end_time_ms"],
                        "confidence": u["confidence"],
                        "sequence_order": i,
                        "resolved_user_id": None,
                    }
                    for i, u in enumerate(utterances_data)
                ]
            )

            job.status = "done"
            job.deepgram_request_id = request_id
            job.completed_at = datetime.utcnow()
            job.processing_ms = transcript_data.get("processing_ms")

            await self.db.commit()
            logger.info(
                f"Job {job.id} updated to done, created "
                f"{len(created_utterances)} utterances"
            )

            await self._publish_transcription_completed_event(
                job.id,
                job.meeting_id,
                transcript.id,
            )

            return {
                "received": True,
                "job_id": str(job.id),
                "transcript_id": str(transcript.id),
                "utterances_count": len(created_utterances),
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def _find_job_by_deepgram_id(self, deepgram_request_id: str):
        return await self.job_repo.get_by_deepgram_request_id(
            deepgram_request_id
        )

    def _parse_deepgram_response(self, payload: DeepgramWebhookPayload) -> dict:
        all_utterances = []
        confidences = []
        speaker_ids = set()
        fallback_transcripts = []
        processing_ms = None

        for channel in payload.result.channels:
            for alternative in channel.alternatives:
                if alternative.transcript:
                    fallback_transcripts.append(alternative.transcript.strip())
                if alternative.confidence is not None:
                    confidences.append(alternative.confidence)

                if alternative.utterances:
                    for utterance in alternative.utterances:
                        speaker_label = f"Speaker_{utterance.speaker}"
                        speaker_ids.add(utterance.speaker)
                        start_time_ms = int(round(utterance.start * 1000))
                        end_time_ms = int(round(utterance.end * 1000))

                        all_utterances.append(
                            {
                                "text": utterance.text,
                                "speaker_label": speaker_label,
                                "start_time_ms": start_time_ms,
                                "end_time_ms": end_time_ms,
                                "confidence": utterance.confidence,
                            }
                        )

                        confidences.append(utterance.confidence)
                        processing_ms = end_time_ms
                else:
                    paragraphs = (alternative.paragraphs or {}).get(
                        "paragraphs",
                        [],
                    )
                    for paragraph in paragraphs:
                        sentences = paragraph.get("sentences", [])
                        text = " ".join(
                            sentence.get("text", "").strip()
                            for sentence in sentences
                            if sentence.get("text")
                        ).strip()
                        if not text:
                            continue

                        speaker = paragraph.get("speaker")
                        speaker_label = (
                            f"Speaker_{speaker}"
                            if speaker is not None
                            else "Speaker_unknown"
                        )
                        if speaker is not None:
                            speaker_ids.add(speaker)

                        start_time_ms = int(
                            round(float(paragraph.get("start", 0)) * 1000)
                        )
                        end_time_ms = int(
                            round(float(paragraph.get("end", 0)) * 1000)
                        )

                        all_utterances.append(
                            {
                                "text": text,
                                "speaker_label": speaker_label,
                                "start_time_ms": start_time_ms,
                                "end_time_ms": end_time_ms,
                                "confidence": alternative.confidence,
                            }
                        )
                        processing_ms = end_time_ms

        full_text = " ".join(u["text"] for u in all_utterances).strip()
        if not full_text:
            full_text = " ".join(
                transcript for transcript in fallback_transcripts if transcript
            ).strip()

        confidence_avg = (
            sum(confidences) / len(confidences)
            if confidences
            else 0.0
        )

        speaker_count = len(speaker_ids)

        if processing_ms is None:
            duration = (payload.metadata or {}).get("duration")
            if duration is None:
                duration = (payload.result.metadata or {}).get("duration")
            if duration is not None:
                processing_ms = int(round(float(duration) * 1000))

        return {
            "full_text": full_text,
            "utterances": all_utterances,
            "confidence_avg": confidence_avg,
            "speaker_count": speaker_count,
            "processing_ms": processing_ms,
        }

    async def _publish_transcription_completed_event(
        self,
        job_id: uuid.UUID,
        meeting_id: uuid.UUID,
        transcript_id: uuid.UUID,
    ) -> None:
        try:
            event_payload = {
                "event": "transcription.completed",
                "job_id": str(job_id),
                "meeting_id": str(meeting_id),
                "transcript_id": str(transcript_id),
                "timestamp": datetime.utcnow().isoformat(),
            }

            await redis_client.publish(
                CHANNEL_TRANSCRIPTION_COMPLETED,
                json.dumps(event_payload),
            )

            logger.info(
                f"Published transcription.completed event for job {job_id}"
            )
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
