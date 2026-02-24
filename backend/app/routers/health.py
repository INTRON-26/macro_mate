from fastapi import APIRouter

router = APIRouter(tags=["default"])

@router.get("/health")
async def health():
    return {"message": "OK"}

@router.get("/status")
async def status():
    """
    Get application status information.
    """
    return {
        "status": "running",
        "api_version": "1.0.0",
        "storage_backend": "Firebase Firestore"
    }
