from pydantic import BaseModel
from typing import List, Optional

class ActionItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None

class SummarizeRequest(BaseModel):
    text: str

class SummarizeResponse(BaseModel):
    overview: str
    key_points: List[str]
    action_items: List[ActionItem]