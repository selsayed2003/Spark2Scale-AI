from fastapi import FastAPI
from app.api.routes import ppt_generation, evaluation
import uvicorn
import os

app = FastAPI(
    title="Spark2Scale AI Agent",
    description="AI-powered startup evaluation and PPT generation",
    version="1.0.0"
)

# Enable CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ppt_generation.router, prefix="/api/v1/ppt", tags=["PPT Generation"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"])

@app.get("/")
def read_root():
    return {
        "message": "Spark2Scale AI Agent Service is Running",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=port)