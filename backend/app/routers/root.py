from fastapi import APIRouter

router = APIRouter(tags=["default"])

@router.get("/")
async def root():
    return {"message": "Landing page of MacroMate API"}
