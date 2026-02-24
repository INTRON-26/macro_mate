from fastapi import APIRouter

router = APIRouter(tags=["default"])

@router.get("/health")
async def health():
    return {"message": "OK"}
