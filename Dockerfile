# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Install minimal dependencies needed for Python packages
#RUN apt-get update && apt-get install -y \
#    python3-distutils \
#    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to ensure pre-built wheels are used
#RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

RUN echo 'Started bot at' `date` >> ./log.txt;  \
    python notify_account.py

# Specify the command to run the application
CMD ["python", "decision_bot.py"]
