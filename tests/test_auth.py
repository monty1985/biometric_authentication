import pytest
import os
from pathlib import Path
import numpy as np
import soundfile as sf

from app.services.auth import AuthenticationService
from app.core.config import settings

@pytest.fixture
def auth_service():
    return AuthenticationService()

@pytest.fixture
def test_audio():
    # Create a simple test audio file
    sample_rate = 16000
    duration = 5  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    
    # Save to temporary file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = Path(settings.UPLOAD_DIR) / "test_audio.wav"
    sf.write(file_path, audio, sample_rate)
    
    yield str(file_path)
    
    # Cleanup
    if file_path.exists():
        os.remove(file_path)

async def test_enroll_user(auth_service, test_audio):
    user_id = "test_user_1"
    success, message = await auth_service.enroll_user(user_id, test_audio)
    assert success
    assert "successfully" in message.lower()
    
    # Verify user info exists
    user_info = auth_service.get_user_info(user_id)
    assert user_info is not None
    assert "enrolled_at" in user_info
    assert "quality_metrics" in user_info

async def test_verify_user(auth_service, test_audio):
    user_id = "test_user_2"
    
    # First enroll the user
    success, _ = await auth_service.enroll_user(user_id, test_audio)
    assert success
    
    # Then verify
    is_verified, confidence, message = await auth_service.verify_user(user_id, test_audio)
    assert is_verified
    assert confidence > settings.SIMILARITY_THRESHOLD
    assert "successful" in message.lower()

async def test_verify_nonexistent_user(auth_service, test_audio):
    user_id = "nonexistent_user"
    is_verified, confidence, message = await auth_service.verify_user(user_id, test_audio)
    assert not is_verified
    assert confidence == 0.0
    assert "not found" in message.lower()

async def test_duplicate_enrollment(auth_service, test_audio):
    user_id = "test_user_3"
    
    # First enrollment
    success, _ = await auth_service.enroll_user(user_id, test_audio)
    assert success
    
    # Try to enroll again
    success, message = await auth_service.enroll_user(user_id, test_audio)
    assert not success
    assert "already enrolled" in message.lower() 