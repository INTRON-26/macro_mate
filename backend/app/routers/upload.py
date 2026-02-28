from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.routers.auth import get_current_user_from_token
from app.models import User
from app.services.supabase_service import supabase_service


router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)


class ImageUploadResponse(BaseModel):
    """Response model for image upload."""
    success: bool
    file_path: str
    public_url: str
    message: str


class ImageDeleteResponse(BaseModel):
    """Response model for image deletion."""
    success: bool
    message: str


class UserImagesResponse(BaseModel):
    """Response model for listing user images."""
    success: bool
    images: List[dict]
    count: int


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Upload an image to Supabase Storage.
    
    **Authentication required**: You must be logged in to upload images.
    
    - **file**: Image file (JPEG, PNG, GIF, or WebP, max 10MB)
    
    Returns the file path and public URL of the uploaded image.
    """
    file_path, public_url = await supabase_service.upload_image(
        file=file,
        user_email=current_user.email
    )
    
    return ImageUploadResponse(
        success=True,
        file_path=file_path,
        public_url=public_url,
        message="Image uploaded successfully"
    )


@router.delete("/image/{file_path:path}", response_model=ImageDeleteResponse)
async def delete_image(
    file_path: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Delete an image from Supabase Storage.
    
    **Authentication required**: You must be logged in to delete images.
    
    - **file_path**: Path of the image to delete (must belong to the current user)
    
    Only the user who uploaded the image can delete it.
    """
    # Verify the file belongs to the current user
    safe_email = current_user.email.split("@")[0].replace(".", "_")
    if not file_path.startswith(safe_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own images"
        )
    
    await supabase_service.delete_image(file_path)
    
    return ImageDeleteResponse(
        success=True,
        message="Image deleted successfully"
    )


@router.get("/images", response_model=UserImagesResponse)
async def list_user_images(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    List all images uploaded by the current user.
    
    **Authentication required**: You must be logged in to view your images.
    
    Returns a list of all images you have uploaded.
    """
    images = await supabase_service.list_user_images(current_user.email)
    
    return UserImagesResponse(
        success=True,
        images=images,
        count=len(images)
    )


@router.post("/multiple-images", response_model=dict)
async def upload_multiple_images(
    files: List[UploadFile] = File(..., description="Multiple image files to upload"),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Upload multiple images to Supabase Storage.
    
    **Authentication required**: You must be logged in to upload images.
    
    - **files**: Multiple image files (JPEG, PNG, GIF, or WebP, max 10MB each)
    
    Returns information about all uploaded images.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files can be uploaded at once"
        )
    
    uploaded_images = []
    errors = []
    
    for file in files:
        try:
            file_path, public_url = await supabase_service.upload_image(
                file=file,
                user_email=current_user.email
            )
            uploaded_images.append({
                "filename": file.filename,
                "file_path": file_path,
                "public_url": public_url
            })
        except HTTPException as e:
            errors.append({
                "filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success": len(uploaded_images) > 0,
        "uploaded_count": len(uploaded_images),
        "error_count": len(errors),
        "uploaded_images": uploaded_images,
        "errors": errors,
        "message": f"Successfully uploaded {len(uploaded_images)} of {len(files)} images"
    }
