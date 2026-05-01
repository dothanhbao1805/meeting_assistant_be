from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List

from app.repositories import member_repo
from app.utils.voice_embedding import compute_embedding_from_bytes, average_embeddings


async def update_voice_embedding(
    db: AsyncSession,
    member_id: str,
    audio_bytes_list: List[bytes],
) -> dict:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Tính embedding cho từng file rồi lấy trung bình
    embeddings = [compute_embedding_from_bytes(b) for b in audio_bytes_list]
    avg_embedding = average_embeddings(embeddings)

    # Cập nhật DB
    member.voice_embedding = avg_embedding
    db.add(member)
    await db.commit()

    return {
        "member_id": str(member.id),
        "full_name": member.full_name,
        "embedding_dim": len(avg_embedding),
        "files_used": len(audio_bytes_list),
        "message": "Voice embedding updated successfully",
    }