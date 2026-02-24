from .root import router as root_router
from .health import router as health_router
from .auth import router as auth_router

routers = [root_router, health_router, auth_router]
