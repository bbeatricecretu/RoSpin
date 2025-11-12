# Use official Python image
FROM python:3.14-slim

# Install PostgreSQL client (if needed)
RUN apt-get update && apt-get install -y postgresql-client

# Set working directory
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY SkyWind/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project (including React static files)
COPY SkyWind/ ./

# Expose port
EXPOSE 8000

# Run Django via Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]