# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add the app directory to Python path
ENV PYTHONPATH=/app

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Set default database path
ENV DB_PATH=/app/data/weather_display.db

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app/main.py"]
