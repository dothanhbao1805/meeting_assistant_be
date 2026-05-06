import httpx
from uuid import UUID
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.speaker import SpeakerResolveRequest


class SpeakerService:
    def __init__(self):
        self.meeting_url = settings.MEETING_SERVICE_URL
        self.transcript_url = settings.TRANSCRIPTION_SERVICE_URL

    async def get_unresolved_logic(self, meeting_id: UUID, token: str):
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. Lấy meeting (participants)
                p_resp = await client.get(
                    f"{self.meeting_url}/internal/meetings/{meeting_id}",
                    headers=headers,
                )

                # 2. All utterances
                t_resp = await client.get(
                    f"{self.transcript_url}/utterances/{meeting_id}/all",
                    headers=headers,
                )

                # 3. Unresolved utterances
                u_resp = await client.get(
                    f"{self.transcript_url}/utterances/{meeting_id}/resolved-user-id-is-null",
                    headers=headers,
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=500,
                detail="Không kết nối được tới service khác",
            )

        # ===== CHECK STATUS =====
        if p_resp.status_code == 401:
            raise HTTPException(401, "Meeting service: Unauthorized")

        if t_resp.status_code == 401 or u_resp.status_code == 401:
            raise HTTPException(401, "Transcript service: Unauthorized")

        if any(r.status_code != 200 for r in (p_resp, t_resp, u_resp)):
            raise HTTPException(
                status_code=500,
                detail={
                    "meeting_status": p_resp.status_code,
                    "transcript_status": t_resp.status_code,
                    "unresolved_status": u_resp.status_code,
                },
            )

        # ===== PARSE DATA =====
        meeting_data = p_resp.json()
        all_participants = meeting_data.get("participants", [])

        speaker_status = t_resp.json()
        unresolved_utterances = u_resp.json()

        # ===== RESOLVED IDS =====
        resolved_user_ids = {
            str(s.get("resolved_user_id"))
            for s in speaker_status
            if s.get("resolved_user_id")
        }

        # ===== FILTER PARTICIPANTS =====
        available_participants = [
            p for p in all_participants
            if str(p.get("user_id")) not in resolved_user_ids
        ]

        # ===== GROUP UTTERANCES BY SPEAKER =====
        groups = {}

        for u in unresolved_utterances:
            label = u.get("speaker_label", "unknown")

            if label not in groups:
                groups[label] = {
                    "speaker_label": label,
                    "sample_utterances": [],
                    "participants_to_choose": available_participants,
                }

            if len(groups[label]["sample_utterances"]) < 3:
                groups[label]["sample_utterances"].append(u.get("text", ""))

        return list(groups.values())

    async def patch_resolve_logic(
        self,
        meeting_id: UUID,
        payload: list[SpeakerResolveRequest],
        token: str,
    ):
        headers = {"Authorization": f"Bearer {token}"}

        enriched_payload = [
            {
                "speaker_label": item.speaker_label,
                "resolved_user_id": str(item.resolved_user_id),
            }
            for item in payload
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.patch(
                    f"{self.transcript_url}/utterances/{meeting_id}/resolve-speaker",
                    json=enriched_payload,
                    headers=headers,
                )

                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Update utterances failed: {resp.text}",
                    )

                data = resp.json()
                print("TRANSCRIPT RESPONSE:", data)
                all_resolved = data.get("all_resolved", False)

        except httpx.ConnectError:
            raise HTTPException(
                status_code=500,
                detail="Cannot connect transcription service",
            )

        return {
            "updated_count": len(payload),
            "all_resolved": all_resolved,
        }