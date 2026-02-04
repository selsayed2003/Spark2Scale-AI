import uvicorn
from app.core.logger import get_logger # Fixed import path

logger = get_logger("main")

def main():
    logger.info("Starting Spark2Scale AI API Server...")
    # reload=True is great for dev, implies 'main.py' is entry point
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()