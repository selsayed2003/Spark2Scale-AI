import os
import uvicorn
from app.core.logger import get_logger

logger = get_logger("main")

def main():
    logger.info("Starting Spark2Scale AI API Server...")
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
