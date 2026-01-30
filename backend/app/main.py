from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine
from app.security import engine
from app.routes import auth, documents, workspaces, users

# Create tables
SQLModel.metadata.create_all(engine)

app = FastAPI(title="Advisor API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(workspaces.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Advisor API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
