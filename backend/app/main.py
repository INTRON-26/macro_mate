from fastapi import FastAPI
from app.routers import routers

app = FastAPI(
    title="MacroMate API",
    description="API for tracking macros and nutrition",
    version="1.0.0"
)

for router in routers:
    app.include_router(router)