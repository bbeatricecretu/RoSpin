# Use official Python image
FROM python:3.14-slim

RUN apt-get update && apt-get install -y postgresql-client

# Set working directory
WORKDIR /app

# Prevent Python from buffering output (for logs)
ENV PYTHONUNBUFFERED=1

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose Django’s default port
EXPOSE 8000

# Run the Django dev server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
