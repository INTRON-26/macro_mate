from fastapi import APIRouter

router = APIRouter(tags=["firebase"])


@router.get("/test-firebase")
async def test_firebase():
    """
    Test Firebase Firestore connection.
    
    Creates a test document in Firestore to verify connectivity.
    """
    from firebase_admin import firestore
    
    db = firestore.client()
    doc_ref = db.collection("test").document("connection_check")
    
    # Check if document exists
    doc = doc_ref.get()
    
    # Write test data
    doc_ref.set({
        "status": "working",
        "timestamp": firestore.SERVER_TIMESTAMP,
        "message": "Firebase connection successful"
    })
    
    return {
        "firebase_status": "connected",
        "message": "Firebase Firestore is working correctly",
        "test_collection": "test",
        "test_document": "connection_check"
    }