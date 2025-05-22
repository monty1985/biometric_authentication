from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from fastapi import HTTPException, Depends
from pathlib import Path

from .api.v1.router import api_router
from .core.config import settings
from .services.auth import AuthenticationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A secure, scalable voice authentication system for enterprise applications",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, replace with specific hosts
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Create a single instance of AuthenticationService
auth_service = AuthenticationService()

@app.post("/api/v1/auth/enroll")
async def enroll_user(
    user_id: str,
    voice_sample: UploadFile = File(...)
):
    try:
        logger.info(f"Starting enrollment for user: {user_id}")
        # Save the uploaded file temporarily
        temp_path = Path(settings.UPLOAD_DIR) / f"{user_id}_temp.wav"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving uploaded file to: {temp_path}")
        with open(temp_path, "wb") as buffer:
            content = await voice_sample.read()
            buffer.write(content)
        
        logger.info("File saved successfully, calling auth service")
        result = await auth_service.enroll_user(user_id, str(temp_path))
        logger.info(f"Auth service response: {result}")
        
        # Clean up
        temp_path.unlink()
        logger.info("Temporary file cleaned up")
        
        if not result[0]:  # If enrollment failed
            raise HTTPException(
                status_code=400,
                detail=result[1]
            )
            
        return {"success": True, "message": result[1]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrollment error for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enrollment failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 