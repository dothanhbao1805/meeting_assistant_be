from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
)


async def summarize_text(text: str) -> dict:
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
                    Bạn là AI trích xuất thông tin từ transcript cuộc họp.

                    Trả về JSON hợp lệ với format:

                    {
                    "overview": "...",
                    "key_points": ["..."],
                    "action_items": [
                        {
                        "task": "...",
                        "assignee": "...",
                        "deadline": "..."
                        }
                    ]
                    }

                    Chỉ trả về JSON, không thêm bất kỳ text nào khác.
                    """,
            },
            {"role": "user", "content": text},
        ],
        temperature=0.2,
    )

    import json

    return json.loads(response.choices[0].message.content)
