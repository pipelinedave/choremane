from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json

router = APIRouter(prefix="/mcp", tags=["mcp"])


class Message(BaseModel):
    role: str
    content: str


class MCPRequest(BaseModel):
    messages: List[Message]


class MCPResponse(BaseModel):
    content: str


@router.post("/generate", response_model=MCPResponse)
async def generate_suggestions(request: MCPRequest):
    try:
        # Find the user's input message
        user_message = next(
            (msg.content for msg in request.messages if msg.role == "user"), None
        )
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Example suggestions based on common household tasks
        suggestions = [
            {"name": "General cleaning", "intervalDays": 7},
            {"name": "Vacuum floors", "intervalDays": 3},
            {"name": "Dust surfaces", "intervalDays": 7},
            {"name": "Clean bathroom", "intervalDays": 7},
            {"name": "Take out trash", "intervalDays": 2},
            {"name": "Change bed sheets", "intervalDays": 7},
            {"name": "Water plants", "intervalDays": 3},
            {"name": "Clean kitchen", "intervalDays": 2},
        ]

        # Return the suggestions as JSON string
        return {"content": json.dumps(suggestions)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
