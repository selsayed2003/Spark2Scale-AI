from fastapi import FastAPI
from app.api.routes import ppt_generation, evaluation
import uvicorn
import os

app = FastAPI(title="Spark2Scale AI Agent")

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
# app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"])
# app.include_router(market_research.router, prefix="/api/v1/market-research", tags=["Market Research"])
# app.include_router(recommendation.router, prefix="/api/v1/recommendation", tags=["Recommendation"])

@app.get("/")
def read_root():
    return {"message": "Spark2Scale AI Agent Service is Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=port)