from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import Dict
import os
import uuid
from pathlib import Path

from ....services.auth import AuthenticationService
from ....core.config import settings

router = APIRouter()
auth_service = AuthenticationService()

# API key security
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    # In production, implement proper API key validation
    if api_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.post("/enroll")
async def enroll_user(
    user_id: str,
    voice_sample: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Enroll a new user with their voice sample
    """
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded file
        file_path = Path(settings.UPLOAD_DIR) / f"{uuid.uuid4()}.wav"
        with open(file_path, "wb") as f:
            content = await voice_sample.read()
            f.write(content)
        
        # Enroll user
        success, message = await auth_service.enroll_user(user_id, str(file_path))
        
        # Clean up
        os.remove(file_path)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "status": "success",
            "message": message,
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_user(
    user_id: str,
    voice_sample: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Verify a user's voice sample
    """
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded file
        file_path = Path(settings.UPLOAD_DIR) / f"{uuid.uuid4()}.wav"
        with open(file_path, "wb") as f:
            content = await voice_sample.read()
            f.write(content)
        
        # Verify user
        is_verified, confidence, message = await auth_service.verify_user(user_id, str(file_path))
        
        # Clean up
        os.remove(file_path)
        
        return {
            "status": "success" if is_verified else "failed",
            "message": message,
            "confidence": confidence,
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_info(
    user_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Get user enrollment information
    """
    user_info = auth_service.get_user_info(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "status": "success",
        "user_id": user_id,
        "info": user_info
    } 