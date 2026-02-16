# 1. Base Image: Python 3.11 for AI project compatibility
FROM python:3.11-slim

# 2. Set Working Directory
WORKDIR /app

# 3. Install System dependencies for AI/Transformers (e.g., build-essential)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and Install Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy your Spark2Scale code
COPY . .

# 6. Expose the port (FastAPI/Flask usually 8000)
EXPOSE 8000

# 7. Start Command
CMD ["python", "main.py"]
