from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.modules.nlp.processor import NLPProcessor
from app.modules.user.user_manager import UserManager
from app.core import state

router = APIRouter()
processor = NLPProcessor()
user_manager = UserManager()

import time

class CommandRequest(BaseModel):
    text: str
    user_id: str = None
    metadata: dict = {}

class CommandResponse(BaseModel):
    success: bool
    active_user: str
    result: dict
    timestamp: float

@router.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Command text cannot be empty")
    
    target_user = request.user_id if request.user_id else state.ACTIVE_USER
    
    # Increment global command counter
    state.COMMAND_COUNT += 1
    
    # 1. Load User Profile
    user_profile = await user_manager.load_user(target_user)
    
    # 2. Delegate to the NLP Module (passing the user profile)
    result = await processor.analyze(request.text, user_profile)
    
    # 3. Record History
    if result.get("intent") != "SWITCH_USER":
        await user_manager.record_command(target_user, request.text, result["intent"])
    
    return CommandResponse(
        success=True,
        active_user=state.ACTIVE_USER,
        result={
            "intent": result.get("intent"),
            "action_taken": result.get("action"),
            "response_message": result.get("message"),
            "user_name": user_profile.get("name", target_user),
            "metadata": result.get("metadata", {})
        },
        timestamp=time.time()
    )
