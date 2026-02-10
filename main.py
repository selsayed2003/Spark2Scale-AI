from fastapi import FastAPI
from app.api.routes import workflow
import uvicorn
import os

app = FastAPI(title="Spark2Scale AI Agent")

# Include the workflow router
app.include_router(workflow.router, prefix="/api/v1", tags=["Workflow"])

@app.get("/")
def read_root():
    return {"message": "Spark2Scale AI Agent Service is Running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
