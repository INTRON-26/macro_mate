import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.models import User
from app.routers.auth import get_current_user_from_token
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True,
)

router = APIRouter(
    prefix="/images",
    tags=["images"]
)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Upload an image to Cloudinary (requires authentication).

    - **file**: Image file (JPEG, PNG, GIF, WEBP, etc.)

    Returns the Cloudinary secure URL and public ID of the uploaded image.
    """
    # Validate content type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {', '.join(allowed_types)}",
        )

    try:
        contents = await file.read()
        result = cloudinary.uploader.upload(
            contents,
            folder="test",
            public_id=file.filename.rsplit(".", 1)[0] if file.filename else None,
            resource_type="image",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}",
        )
    finally:
        await file.close()

    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
        "format": result.get("format"),
        "width": result.get("width"),
        "height": result.get("height"),
        "uploaded_by": current_user.email,
    }
