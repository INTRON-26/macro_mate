from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

# API metadata and tags
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and monitoring endpoints",
    },
    {
        "name": "items",
        "description": "Operations with items. Create, read, update, and delete items.",
    },
]

app = FastAPI(
    title="MacroMate API",
    description="""
    ## MacroMate Backend API
    
    This API provides endpoints for managing macro tracking and nutrition data.
    
    ### Features:
    * **Health Monitoring**: Check service health and status
    * **Item Management**: CRUD operations for items
    * **Real-time Updates**: WebSocket support (coming soon)
    
    ### Authentication:
    Authentication endpoints will be added in future versions.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "MacroMate Team",
        "url": "https://github.com/INTRON-26/macro_mate",
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., example="healthy", description="Service health status")
    message: str = Field(..., example="Service is running", description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "Service is running"
            }
        }

class Item(BaseModel):
    """Item model"""
    id: Optional[int] = Field(None, example=1)
    name: str = Field(..., example="Apple", min_length=1, max_length=100)
    description: Optional[str] = Field(None, example="A fresh red apple")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., example="Item not found")

@app.get(
    "/",
    summary="Root Endpoint",
    description="Welcome endpoint that provides API information",
    response_description="Welcome message and API info",
)
async def root():
    """
    Root endpoint that returns a welcome message.
    
    Use this to verify the API is accessible.
    """
    return {
        "message": "Welcome to MacroMate API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health Check",
    description="Check if the service is running and healthy",
    response_description="Service health status",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
    - **status**: Current service status
    - **message**: Detailed status message
    """
    return HealthResponse(
        status="healthy",
        message="Service is running"
    )

@app.get(
    "/items/{item_id}",
    tags=["items"],
    summary="Get Item by ID",
    description="Retrieve a specific item by its unique identifier",
    response_description="The requested item",
    responses={
        200: {
            "description": "Item found successfully",
            "content": {
                "application/json": {
                    "example": {"item_id": 1, "name": "Item 1"}
                }
            },
        },
        404: {
            "description": "Item not found",
            "model": ErrorResponse,
        },
    },
)
async def read_item(item_id: int):
    """
    Get an item by its ID.
    
    Parameters:
    - **item_id**: The unique identifier of the item
    
    Returns the item with the specified ID.
    """
    return {"item_id": item_id, "name": f"Item {item_id}"}

@app.post(
    "/items",
    response_model=Item,
    tags=["items"],
    summary="Create New Item",
    description="Create a new item with the provided data",
    response_description="The created item",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Item created successfully",
            "model": Item,
        },
        400: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
async def create_item(item: Item):
    """
    Create a new item.
    
    Request body:
    - **name**: Required. The name of the item (1-100 characters)
    - **description**: Optional. A detailed description of the item
    - **id**: Optional. Will be auto-generated if not provided
    
    Returns the created item with all fields populated.
    """
    # Add your business logic here
    if item.id is None:
        item.id = 1  # In real app, this would be auto-generated
# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to MacroMate API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Service is running"
    )

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """Get an item by ID"""
    return {"item_id": item_id, "name": f"Item {item_id}"}

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item"""
    # Add your business logic here
    return item

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
