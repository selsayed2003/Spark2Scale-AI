# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML/AI packages and Playwright
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt (FULL requirements with all ML packages)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p outputs logs output/recommendations

# Expose ports (8000 for FastAPI, 11434 for Ollama)
EXPOSE 8000 11434

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Ollama in background\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to start..."\n\
sleep 5\n\
\n\
# Pull the model you need (replace with your model)\n\
ollama pull llama2\n\
\n\
# Start gunicorn\n\
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.api.main:app --bind 0.0.0.0:8000 --timeout 300\n\
' > /app/startup.sh && chmod +x /app/startup.sh

# Run startup script
CMD ["/app/startup.sh"]
