from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.services.openai_service import get_openai_service, OpenAIService
from app.services.lms_service import get_lms_client, LMSClient

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    openai_service: OpenAIService = Depends(get_openai_service),
    lms_client: LMSClient = Depends(get_lms_client)
):
    try:
        logger.info("Received chat request")
        messages = [m.model_dump() for m in request.messages]
        # Unified chat handles everything
        response_text = await openai_service.chat(messages, lms_client=lms_client)
        logger.info("Successfully generated chat response")
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
