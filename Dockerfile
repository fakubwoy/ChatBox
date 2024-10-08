# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 12345

# Ensure upload and static directories have proper permissions
RUN mkdir -p uploads static
RUN chmod -R 755 uploads static

# Start the Flask app using Waitress
# Replace 'server:app' with 'guniserver:app' if 'guniserver.py' is your main app
CMD ["waitress-serve", "--host=0.0.0.0", "--port=12345", "guniserver:app"]