from fastapi import FastAPI
from routes.health import router as health_router
from routes.db import router as db_router

app = FastAPI(title="My API", version="1.0.0")

# Register routes
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(db_router, prefix="/db", tags=["db"])

@app.get("/")
def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)