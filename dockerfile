# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies for tkinter and display
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY README.md .

# Create a volume mount point for file operations
VOLUME ["/data"]

# Set environment variables for display
ENV DISPLAY=:0
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
