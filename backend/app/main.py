from fastapi import FastAPI
from app.routers import routers

tags_metadata = [
    {
        "name": "authentication",
        "description": "Operations for user authentication including registration and login.",
    },
    {
        "name": "upload",
        "description": "Image upload operations to Supabase Storage. Requires authentication.",
    },
    {
        "name": "default",
        "description": "General application endpoints.",
    },
]

app = FastAPI(
    title="MacroMate API",
    description="""
MacroMate API helps you track your macros and nutrition. 🥗

## Features

* **User Authentication**: Register and login to access personalized features
* **Image Upload**: Upload and manage images with Supabase Storage
* **Health Monitoring**: Check API health status
* **Nutrition Tracking**: Track your daily macros and nutritional intake (coming soon)

## Authentication

Most endpoints require authentication. Use the `/auth/login` endpoint to get an access token,
then use the "Authorize" button above to add your token.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
)

for router in routers:
    app.include_router(router)