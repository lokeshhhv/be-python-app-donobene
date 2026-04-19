# Dockerfile for FastAPI app with Python 3.9.6
FROM python:3.9.6-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (WeasyPrint and others)
RUN apt-get update && apt-get install -y \
	gcc \
	libmariadb-dev \
	libpango-1.0-0 \
	libpangocairo-1.0-0 \
	libcairo2 \
	libgdk-pixbuf2.0-0 \
	libffi-dev \
	shared-mime-info \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY ./src /app/src

# Expose port
EXPOSE 8000

# Set environment variables for DB connection (can be overridden by docker-compose)
ENV DB_HOST=db
ENV DB_PORT=3306
ENV DB_USER=root
ENV DB_PASSWORD=root
ENV DB_NAME=testdb

# Start FastAPI with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
