import os
from typing import Optional, Tuple
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from fastapi import UploadFile, HTTPException, status
import uuid
from datetime import datetime
from dotenv import load_dotenv
from json import JSONDecodeError
from httpx import HTTPError
from storage3.utils import StorageException
from storage3._sync import file_api as storage_file_api

load_dotenv()


def _patch_storage3_request() -> None:
    """Patch storage3 to avoid UnboundLocalError on request failures."""
    if getattr(storage_file_api.SyncBucketActionsMixin._request, "_patched", False):
        return

    def _safe_request(
        self,
        method,
        url,
        headers=None,
        json=None,
        files=None,
        **kwargs,
    ):
        response = None
        try:
            response = self._client.request(
                method, url, headers=headers or {}, json=json, files=files, **kwargs
            )
            response.raise_for_status()
        except HTTPError as exc:
            if response is None and hasattr(exc, "response"):
                response = exc.response

            if response is not None:
                try:
                    resp = response.json()
                    raise StorageException({**resp, "statusCode": response.status_code})
                except JSONDecodeError:
                    raise StorageException({"statusCode": response.status_code})

            raise StorageException({"statusCode": 0, "message": str(exc)})

        return response

    _safe_request._patched = True
    storage_file_api.SyncBucketActionsMixin._request = _safe_request

class SupabaseService:
    """Service for handling Supabase operations including file uploads."""
    
    def __init__(self):
        """Initialize Supabase client."""

        _patch_storage3_request()

        self.supabase_url = os.getenv("SUPABASE_URL")
        # Use service role key for server-side storage access; fall back to publishable key
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "images")

        if not self.supabase_url or not self.supabase_key:
            print("Warning: Supabase credentials not configured")
            self.client: Optional[Client] = None
        else:
            storage_timeout = int(os.getenv("SUPABASE_STORAGE_TIMEOUT_SECONDS", "60"))
            options = ClientOptions(storage_client_timeout=storage_timeout)
            self.client = create_client(self.supabase_url, self.supabase_key, options)
    
    def _validate_client(self):
        """Validate that Supabase client is initialized."""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase service not configured. Please check environment variables."
            )
    
    async def upload_image(
        self,
        file: UploadFile,
        user_email: str,
        allowed_types: list = None
    ) -> Tuple[str, str]:
        """
        Upload an image to Supabase Storage.

        Args:
            file: The uploaded file
            user_email: Email of the user uploading the file
            allowed_types: List of allowed MIME types

        Returns:
            Tuple of (file_path, public_url)
        """
        self._validate_client()
        content_type = file.headers.get("content-type", "")
        print("File content type:", content_type)
        print("Allowed types:", allowed_types)
        # Default allowed types if not specified
        if allowed_types is None:
            allowed_types = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/gif",
                "image/webp"
            ]

        # Validate file type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        print(f"File size: {len(file_content)} bytes")
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_email = user_email.split("@")[0].replace(".", "_")
        file_path = f"{safe_email}/{timestamp}_{unique_id}.{file_extension}"

        try:
            print(f"Uploading file to Supabase Storage at path: {file_path}")
            # Upload to Supabase Storage with proper file options
            result = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                file_content,
                {
                    "contentType": file.content_type,
                    "cacheControl": "3600"
                }
            )

            # Check for upload errors
            if result and isinstance(result, dict) and result.get("error"):
                error_msg = result.get("error")
                print(f"Error uploading image: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload image: {error_msg}"
                )

            # Construct public URL manually
            public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{file_path}"

            return file_path, public_url

        except StorageException as e:
            error_detail = e.args[0] if e.args else str(e)
            print(f"Error uploading image: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {error_detail}"
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
    
    async def delete_image(self, file_path: str) -> bool:
        """
        Delete an image from Supabase Storage.
        
        Args:
            file_path: Path of the file to delete
            
        Returns:
            True if successful
        """
        self._validate_client()
        
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}"
            )
    
    async def list_user_images(self, user_email: str) -> list:
        """
        List all images uploaded by a user.
        
        Args:
            user_email: Email of the user
            
        Returns:
            List of file information
        """
        self._validate_client()
        
        safe_email = user_email.split("@")[0].replace(".", "_")
        
        try:
            files = self.client.storage.from_(self.bucket_name).list(safe_email)
            return files
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list images: {str(e)}"
            )


# Singleton instance
supabase_service = SupabaseService()
