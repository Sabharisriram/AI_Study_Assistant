from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.agent_service import agent
from app.services.auth_service import get_user
import asyncio

router = APIRouter()


class Query(BaseModel):
    question: str


def get_current_user(authorization: str = None) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user  = get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


async def stream_response(text: str):
    for word in text.split():
        yield word + " "
        await asyncio.sleep(0.03)


@router.post("/stream")
async def chat_stream(query: Query, authorization: str = Header(None)):
    user    = get_current_user(authorization)
    user_id = user["user_id"]

    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    answer = agent(user_id, query.question)

    return StreamingResponse(
        stream_response(answer),
        media_type="text/plain"
    )