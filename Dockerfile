FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/pastes /app/secrets

# Make scripts executable
RUN chmod +x manage.py pull.sh push.sh start.sh

# Expose port
EXPOSE 8050

# Start the application using the startup script
CMD ["./start.sh"]
