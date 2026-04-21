from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, AliasPath, BaseModel, Field


class UtteranceData(BaseModel):
    """Utterance from Deepgram response."""

    start: float
    end: float
    confidence: float
    text: str
    speaker: int


class AlternativeData(BaseModel):
    """Alternative transcription."""

    confidence: float
    transcript: str
    words: Optional[List[Dict[str, Any]]] = []
    paragraphs: Optional[Dict[str, Any]] = None
    utterances: Optional[List[UtteranceData]] = []


class ChannelData(BaseModel):
    """Channel data from Deepgram."""

    alternatives: List[AlternativeData]
    detected_language: Optional[str] = None


class ResultData(BaseModel):
    """Transcription result payload."""

    channels: List[ChannelData]
    metadata: Optional[Dict[str, Any]] = None


class DeepgramWebhookPayload(BaseModel):
    """Deepgram webhook callback payload."""

    request_id: str = Field(
        validation_alias=AliasChoices(
            "request_id",
            AliasPath("metadata", "request_id"),
        )
    )
    result: ResultData = Field(
        validation_alias=AliasChoices("result", "results")
    )
    metadata: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Response for Deepgram."""

    received: bool
