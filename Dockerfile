# ShopTrack AI Maintenance Assistant
# MS628 Final Project

# Use a lightweight Python image.
FROM python:3.13-slim

# Set the working folder inside the container.
WORKDIR /app

# Copy the Python requirements first.
COPY requirements.txt .

# Install the required Python packages.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application into the container.
COPY app.py .

# Copy the HTML template folder.
COPY templates ./templates

# Flask uses port 5000.
EXPOSE 5000

# Start ShopTrack when the container runs.
CMD ["python", "app.py"]