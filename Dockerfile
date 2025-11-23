FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY SkyWind/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY SkyWind/ ./

# Expose port
EXPOSE 8000

# Run Django
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]