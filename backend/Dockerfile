# Use an official, slim Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy only the requirements file first to leverage Docker's caching
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# The command to run your application (Railway will override this with its Start Command or Procfile)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT