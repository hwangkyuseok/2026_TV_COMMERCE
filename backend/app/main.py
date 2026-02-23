from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import mock_api

app = FastAPI(
    title="TV Commerce Mock API",
    description="Smart TV Commerce Platform - Mock Data API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_api.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
