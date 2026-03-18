# backend/app/main.py

# External imports
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
# Internal imports
from app.security import engine
from app.routes import auth, documents, workspaces, users, pipeline
from backend.app.storage import init_storage

# Import models so they register with SQLModel.metadata
import app.models  # noqa: F401
from advisor_pipeline.mcp_servers.calculator_server.tools.models import Formula  # noqa: F401

# Create tables
SQLModel.metadata.create_all(engine)

# Init MINIO storage
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_storage()
    yield

# FastAPI app with lifespan for startup tasks
app = FastAPI(title="Advisor API", version="0.1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(workspaces.router)
app.include_router(users.router)
app.include_router(pipeline.router)

# Root and health check endpoints
@app.get("/")
def read_root():
    return {"message": "Advisor API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
