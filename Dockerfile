FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing, OCR, and audio/video
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    ffmpeg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and upgrade npm to latest (Debian's npm 9 is too old for Reflex)
RUN apt-get update && apt-get install -y nodejs npm \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project (rxconfig.py must be in the working directory)
COPY . .

# Expose Reflex default port
EXPOSE 3000

# Run Reflex in dev mode with separate ports to avoid Bun port conflict
# Remove .web cache first to force recompilation of frontend changes
CMD rm -rf .web && reflex run
