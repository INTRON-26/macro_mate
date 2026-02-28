from .root import router as root_router
from .health import router as health_router
from .auth import router as auth_router
from .test_firebase import router as test_firebase_router
from .upload import router as upload_router

routers = [root_router, health_router, auth_router, test_firebase_router, upload_router]
