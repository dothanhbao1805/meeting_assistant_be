import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MemberEmbedding:
    member_id: str
    full_name: str
    embedding: List[float]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def find_best_match(
    speaker_embedding: List[float],
    members: List[MemberEmbedding],
    threshold: float = 0.75,       # cosine similarity tối thiểu
) -> Optional[str]:
    """
    So sánh speaker_embedding với tất cả members.
    Trả về member_id có similarity cao nhất nếu >= threshold,
    ngược lại trả None (không đủ chắc chắn).
    """
    best_id, best_score = None, -1.0

    for m in members:
        if not m.embedding:
            continue
        score = cosine_similarity(speaker_embedding, m.embedding)
        if score > best_score:
            best_score = score
            best_id = m.member_id

    return best_id if best_score >= threshold else None