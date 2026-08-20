# Use a clean, official Python image
FROM python:3.13-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tell the container where to look for command-line tool executables
ENV PATH="/root/.local/bin:$PATH"

# Set workspace directory inside the container
WORKDIR /app

# Install operating system dependencies needed for PostgreSQL and compiling tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . /app/

# Expose the standard web port
EXPOSE 8000
