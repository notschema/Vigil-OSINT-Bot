FROM node:18-slim AS frontend-builder

# Set working directory
WORKDIR /frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Ensure public directory exists
RUN mkdir -p public

# Build the frontend - using standalone output mode from next.config.js
RUN npm run build

# Python stage
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    git \
    gcc \
    build-essential \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8000
ENV FRONTEND_PORT=8080

# Working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    websockets \
    psutil \
    python-dotenv

# Make sure maigret is properly installed
RUN pip install --no-cache-dir maigret==0.4.4

# Create directories
RUN mkdir -p temp logs config

# Copy entire project (except frontend which we'll copy specifically)
COPY . .
RUN rm -rf /app/frontend || true
RUN mkdir -p /app/frontend

# Copy frontend build artifacts - CORRECTED FOR STANDALONE MODE
COPY --from=frontend-builder /frontend/.next/standalone /app/frontend
COPY --from=frontend-builder /frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /frontend/public /app/frontend/public

# Debug: Check frontend structure
RUN echo "Checking frontend directory structure..."
RUN ls -la /app/frontend
RUN ls -la /app/frontend/.next/static || echo "No static directory"
RUN if [ -f "/app/frontend/server.js" ]; then echo "Standalone server.js found"; else echo "WARNING: standalone server.js not found"; fi

# Set execute permissions for scripts
RUN chmod +x vigil.py
RUN chmod +x api/main.py
RUN chmod +x start.sh

# Expose ports
EXPOSE 8000 8080

# Start application
CMD ["./start.sh"]
