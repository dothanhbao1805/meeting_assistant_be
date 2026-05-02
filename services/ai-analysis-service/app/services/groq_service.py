import asyncio
import json
import re
import logging
from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=settings.GROQ_API_KEY)


def _build_conversation(utterances: list[dict], participants: list[dict] | None = None) -> str:
    user_map = {}
    if participants:
        for p in participants:
            user_map[str(p["user_id"])] = p["full_name"]

    lines = []
    for u in utterances:
        resolved_user_id = str(u.get("resolved_user_id") or "")

        if resolved_user_id and resolved_user_id in user_map:
            speaker = user_map[resolved_user_id]
        else:
            speaker = u.get("speaker_label") or "Unknown"

        text = u.get("text", "").strip()
        start = u.get("start_time_ms", 0) // 1000
        lines.append(f"[{start}s] {speaker}: {text}")
    return "\n".join(lines)


def _parse_json(content: str | None, label: str) -> any:
    if not content or not content.strip():
        raise ValueError(f"[{label}] Groq trả về content rỗng")

    logger.debug(f"[{label}] Raw content: {repr(content[:300])}")

    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"[{label}] JSON không hợp lệ. Content: {repr(content[:300])} | Lỗi: {e}"
        )


SUMMARY_PROMPT = """Bạn là trợ lý phân tích cuộc họp. Dựa vào nội dung hội thoại sau, hãy trả về JSON với cấu trúc:
{{
  "summary_text": "tóm tắt ngắn gọn toàn bộ cuộc họp",
  "key_decisions": ["quyết định 1", "quyết định 2"],
  "attendees_mentioned": ["tên người 1", "tên người 2"],
  "topics_covered": ["chủ đề 1", "chủ đề 2"],
  "language": "vi"
}}

Chỉ trả về JSON, không giải thích thêm.

Nội dung cuộc họp:
{conversation}"""


TASK_PROMPT = """Bạn là trợ lý trích xuất công việc từ cuộc họp. Dựa vào nội dung hội thoại sau, hãy trả về JSON array:
[
  {{
    "title": "tên công việc ngắn gọn",
    "description": "mô tả chi tiết",
    "raw_assignee_text": "tên người được giao (hoặc null)",
    "deadline_raw": "deadline dạng text (hoặc null)",
    "priority": "high | medium | low",
    "ai_confidence": 0.0
  }}
]

Chỉ trả về JSON array, không giải thích thêm.
{participant_hint}
Nội dung cuộc họp:
{conversation}"""


async def analyze_meeting(
    utterances: list[dict],
    model: str,
    participants: list[dict] | None = None,
) -> tuple[dict, list[dict], int, int]:
    conversation = _build_conversation(utterances, participants)
    logger.info(
        f"[groq_service] Conversation length: {len(conversation)} chars, {len(utterances)} utterances"
    )

    # Build participant hint cho task prompt
    if participants:
        names = ", ".join([p["full_name"] for p in participants if p.get("full_name")])
        participant_hint = (
            f"\nDanh sách người tham gia cuộc họp: {names}."
            f"\nKhi xác định assignee, hãy dùng ĐÚNG tên trong danh sách trên."
            f"\nNếu không rõ người được giao, để null.\n"
        )
        logger.info(f"[groq_service] Participants hint: {names}")
    else:
        participant_hint = ""
        logger.warning("[groq_service] Không có participants — Groq sẽ tự đoán assignee")

    summary_msg = [
        {"role": "user", "content": SUMMARY_PROMPT.format(conversation=conversation)}
    ]
    task_msg = [
        {
            "role": "user",
            "content": TASK_PROMPT.format(
                conversation=conversation,
                participant_hint=participant_hint,
            ),
        }
    ]

    summary_resp, task_resp = await asyncio.gather(
        client.chat.completions.create(model=model, messages=summary_msg),
        client.chat.completions.create(model=model, messages=task_msg),
    )

    summary_content = summary_resp.choices[0].message.content
    task_content = task_resp.choices[0].message.content

    logger.info(f"[groq_service] summary finish_reason={summary_resp.choices[0].finish_reason}")
    logger.info(f"[groq_service] task finish_reason={task_resp.choices[0].finish_reason}")

    summary_data = _parse_json(summary_content, "summary")
    tasks_data = _parse_json(task_content, "tasks")

    if not isinstance(tasks_data, list):
        logger.warning(f"[groq_service] tasks_data không phải list: {type(tasks_data)}")
        tasks_data = []

    input_tokens = summary_resp.usage.prompt_tokens + task_resp.usage.prompt_tokens
    output_tokens = summary_resp.usage.completion_tokens + task_resp.usage.completion_tokens

    logger.info(
        f"[groq_service] Done — tokens in={input_tokens} out={output_tokens}, tasks={len(tasks_data)}"
    )

    return summary_data, tasks_data, input_tokens, output_tokens