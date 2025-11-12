# Use official Python image
FROM python:3.14-slim

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY Skywind/ ./Skywind/

EXPOSE 8000

# Run Django with Gunicorn (better than dev server)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
