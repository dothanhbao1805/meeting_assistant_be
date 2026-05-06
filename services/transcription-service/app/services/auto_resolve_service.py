import os
import uuid
import tempfile
import logging
import httpx
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.utterance import Utterance
from app.utils.audio_crop import crop_audio_bytes
from app.utils.voice_embedding import compute_embedding_from_bytes, average_embeddings
from app.utils.speaker_matcher import MemberEmbedding, find_best_match

logger = logging.getLogger(__name__)

COMPANY_SERVICE_URL = os.getenv(
    "COMPANY_SERVICE_URL", "http://company-service:8003/api/v1"
)
MEETING_SERVICE_URL = os.getenv(
    "MEETING_SERVICE_URL", "http://meeting-service:8005/api/v1"
)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SIMILARITY_THRESHOLD = float(os.getenv("SPEAKER_SIMILARITY_THRESHOLD", "0.75"))
UTTERANCES_PER_SPEAKER = 3


async def _get_audio_url(meeting_file_id: str, token: str) -> str:
    request_url = f"{MEETING_SERVICE_URL}/meeting-files/{meeting_file_id}"
    logger.info(
        "Fetching meeting file metadata", extra={"meeting_file_id": meeting_file_id}
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            request_url,
            headers={"Authorization": token},
            timeout=10,
        )
        resp.raise_for_status()
    data = resp.json()
    bucket = data["storage_bucket"]
    path = data["storage_path"]
    audio_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    logger.info("Built audio URL", extra={"audio_url_preview": audio_url[:200]})
    return audio_url


async def _download_audio(audio_url: str) -> str:
    if not audio_url or not str(audio_url).startswith(("http://", "https://")):
        raise ValueError(f"Invalid audio URL: {audio_url}")
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY is not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            audio_url,
            headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            timeout=120,
            follow_redirects=True,
        )
        resp.raise_for_status()

    suffix = ".mp3" if "mp3" in audio_url else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(resp.content)
        logger.info(
            "Audio written to temp file",
            extra={"tmp_audio_path": tmp.name, "size_bytes": len(resp.content)},
        )
        return tmp.name


async def _fetch_participant_user_ids(meeting_id: str, token: str) -> List[str]:

    # Mới: dùng internal endpoint — không cần auth
    request_url = f"{MEETING_SERVICE_URL}/internal/meetings/{meeting_id}"

    logger.info("Fetching meeting participants", extra={"meeting_id": meeting_id})
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            request_url,
            timeout=10,
        )
        resp.raise_for_status()

    data = resp.json()
    participants = data.get("participants", [])
    user_ids = [p["user_id"] for p in participants if p.get("user_id")]
    logger.info(
        "Fetched participant user_ids",
        extra={"meeting_id": meeting_id, "participant_count": len(user_ids)},
    )
    return user_ids


async def _fetch_members_with_embeddings(
    company_id: str, token: str
) -> Dict[str, dict]:
    """Lấy members của công ty có voice_embedding, keyed by user id."""
    request_url = f"{COMPANY_SERVICE_URL}/members"
    logger.info("Fetching company members", extra={"company_id": company_id})
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            request_url,
            params={"company_id": company_id},
            headers={"Authorization": token},
            timeout=10,
        )
        resp.raise_for_status()

    member_map: Dict[str, dict] = {}
    for m in resp.json():
        if m.get("voice_embedding"):
            member_map[m["id"]] = m
    logger.info(
        "Company members with embeddings",
        extra={"company_id": company_id, "member_count": len(member_map)},
    )
    return member_map


async def _build_candidate_embeddings(
    meeting_id: str,
    company_id: str,
    token: str,
) -> List[MemberEmbedding]:
    """Join participants ∩ members có voice_embedding."""
    participant_user_ids = await _fetch_participant_user_ids(meeting_id, token)
    member_map = await _fetch_members_with_embeddings(company_id, token)

    candidates: List[MemberEmbedding] = []
    for user_id in participant_user_ids:
        member = member_map.get(user_id)
        if member:
            candidates.append(
                MemberEmbedding(
                    member_id=member["id"],
                    full_name=member.get("full_name", ""),
                    embedding=member["voice_embedding"],
                )
            )

    logger.info(
        "Candidate embeddings after join",
        extra={
            "meeting_id": meeting_id,
            "participants_total": len(participant_user_ids),
            "candidates_with_embedding": len(candidates),
        },
    )
    return candidates


# ── Main service ─────────────────────────────────────────────────────────────
async def auto_resolve_speakers(
    db: AsyncSession,
    transcript_id: uuid.UUID,
    meeting_id: str,
    company_id: str,
    meeting_file_id: str,
    token: str = "",
) -> dict:
    logger.info(
        "Starting auto resolve speakers",
        extra={
            "transcript_id": str(transcript_id),
            "meeting_id": meeting_id,
            "company_id": company_id,
            "meeting_file_id": meeting_file_id,
        },
    )

    # ── 1. Lấy utterances ────────────────────────────────────────────────────
    result = await db.execute(
        select(Utterance)
        .where(Utterance.transcript_id == transcript_id)
        .order_by(Utterance.sequence_order)
    )
    utterances: List[Utterance] = result.scalars().all()
    logger.info("Loaded utterances", extra={"count": len(utterances)})

    if not utterances:
        return {"resolved": 0, "message": "No utterances found"}

    # ── 2. Lấy audio ─────────────────────────────────────────────────────────
    audio_url = await _get_audio_url(meeting_file_id, token)
    tmp_audio_path = await _download_audio(audio_url)

    try:
        # ── 3. Nhóm utterances theo speaker_label ────────────────────────────
        speaker_groups: Dict[str, List[Utterance]] = defaultdict(list)
        for u in utterances:
            if u.speaker_label and u.start_time_ms is not None:
                speaker_groups[u.speaker_label].append(u)
        logger.info("Speaker groups", extra={"labels": list(speaker_groups.keys())})

        # ── 4. Build candidates: participant ∩ member có embedding ────────────
        candidates = await _build_candidate_embeddings(meeting_id, company_id, token)
        if not candidates:
            return {"resolved": 0, "message": "No participants with voice embeddings"}

        # ── 5. Tính embedding cho từng speaker rồi so sánh ───────────────────
        speaker_to_user: Dict[str, Optional[str]] = {}

        for speaker_label, utt_list in speaker_groups.items():
            samples = sorted(
                utt_list,
                key=lambda u: (u.end_time_ms or 0) - (u.start_time_ms or 0),
                reverse=True,
            )[:UTTERANCES_PER_SPEAKER]

            embeddings = []
            for utt in samples:
                if utt.start_time_ms is None or utt.end_time_ms is None:
                    continue
                try:
                    audio_bytes = crop_audio_bytes(
                        tmp_audio_path, utt.start_time_ms, utt.end_time_ms
                    )
                    emb = compute_embedding_from_bytes(audio_bytes)
                    embeddings.append(emb)
                except Exception as e:
                    logger.warning(
                        "Crop failed",
                        extra={"utterance_id": str(utt.id), "error": str(e)},
                    )

            if not embeddings:
                speaker_to_user[speaker_label] = None
                continue

            avg_emb = average_embeddings(embeddings)
            matched_user_id = find_best_match(
                avg_emb, candidates, threshold=SIMILARITY_THRESHOLD
            )
            speaker_to_user[speaker_label] = matched_user_id
            logger.info(
                "Speaker matched",
                extra={
                    "speaker_label": speaker_label,
                    "matched_user_id": matched_user_id,
                },
            )

        # ── 6. Gán resolved_user_id hàng loạt ────────────────────────────────
        total_resolved = 0
        for speaker_label, user_id in speaker_to_user.items():
            if user_id is None:
                continue
            await db.execute(
                update(Utterance)
                .where(
                    Utterance.transcript_id == transcript_id,
                    Utterance.speaker_label == speaker_label,
                )
                .values(resolved_user_id=uuid.UUID(user_id))
            )
            total_resolved += sum(
                1 for u in utterances if u.speaker_label == speaker_label
            )

        await db.commit()
        logger.info("Commit done", extra={"utterances_resolved": total_resolved})

    finally:
        if os.path.exists(tmp_audio_path):
            os.unlink(tmp_audio_path)
            logger.info("Deleted temp audio", extra={"path": tmp_audio_path})

    return {
        "transcript_id": str(transcript_id),
        "speakers_processed": len(speaker_groups),
        "speakers_resolved": sum(1 for v in speaker_to_user.values() if v),
        "utterances_resolved": total_resolved,
        "detail": {label: uid for label, uid in speaker_to_user.items()},
    }
