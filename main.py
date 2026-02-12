from fastapi import FastAPI
from app.api.routes import workflow
import uvicorn

from app.core.logger import get_logger # Fixed import path
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "spark2scale"
logger = get_logger("main")

def main():
    logger.info("Starting Spark2Scale AI API Server...")
    # reload=True is great for dev, implies 'main.py' is entry point
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)

app = FastAPI(title="Spark2Scale AI Agent")

# Include the workflow router
app.include_router(workflow.router, prefix="/api/v1", tags=["Workflow"])

@app.get("/")
def read_root():
    return {"message": "Spark2Scale AI Agent Service is Running"}

if __name__ == "__main__":
    main()

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

