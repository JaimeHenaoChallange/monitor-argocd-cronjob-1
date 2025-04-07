# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install Python dependencies and clean up build dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Define the command to run the monitor script
CMD ["python", "monitor.py"]
