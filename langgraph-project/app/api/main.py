from fastapi import FastAPI
from app.api.routes import workflow
import uvicorn

app = FastAPI(title="Spark2Scale AI Agent")

app.include_router(workflow.router, prefix="/api/v1", tags=["Workflow"])

@app.get("/")
def read_root():
    return {"message": "Spark2Scale AI Agent Service is Running"}
