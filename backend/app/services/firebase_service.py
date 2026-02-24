import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase Firestore operations."""
    
    def __init__(self):
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            # Check if running locally with service account key
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"Firebase initialized with credentials from {cred_path}")
            else:
                # Try application default credentials (for production/cloud deployment)
                try:
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with application default credentials")
                except Exception as e:
                    logger.error(f"Firebase initialization failed: {e}")
                    logger.error("Firebase credentials not found!")
                    logger.error("Please set up firebase-credentials.json or configure Application Default Credentials.")
                    logger.error("See FIREBASE_SETUP.md for instructions.")
                    raise RuntimeError(
                        "Firebase initialization failed. Please set up Firebase credentials. "
                        "See backend/FIREBASE_SETUP.md for instructions."
                    ) from e
        
        self.db = firestore.client()
        self.users_collection = self.db.collection('users')
        logger.info("Firestore client initialized successfully")
    
    async def create_user(self, email: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in Firestore.
        
        Args:
            email: User's email (used as document ID)
            user_data: Dictionary containing user information
            
        Returns:
            The created user data
        """
        doc_ref = self.users_collection.document(email)
        doc_ref.set(user_data)
        return user_data
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email.
        
        Args:
            email: User's email
            
        Returns:
            User data dictionary or None if not found
        """
        doc_ref = self.users_collection.document(email)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username.
        
        Args:
            username: User's username
            
        Returns:
            User data dictionary or None if not found
        """
        query = self.users_collection.where('username', '==', username).limit(1)
        docs = query.stream()
        
        for doc in docs:
            return doc.to_dict()
        return None
    
    async def update_user(self, email: str, update_data: Dict[str, Any]) -> bool:
        """
        Update user data.
        
        Args:
            email: User's email
            update_data: Dictionary containing fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.users_collection.document(email)
            doc_ref.update(update_data)
            return True
        except Exception:
            return False
    
    async def delete_user(self, email: str) -> bool:
        """
        Delete a user.
        
        Args:
            email: User's email
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.users_collection.document(email)
            doc_ref.delete()
            return True
        except Exception:
            return False
    
    async def user_exists(self, email: str) -> bool:
        """
        Check if a user exists.
        
        Args:
            email: User's email
            
        Returns:
            True if user exists, False otherwise
        """
        doc_ref = self.users_collection.document(email)
        doc = doc_ref.get()
        return doc.exists


# Singleton instance
firebase_service = FirebaseService()
