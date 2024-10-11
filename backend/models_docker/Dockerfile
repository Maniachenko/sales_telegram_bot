# Use a base image for CPU-only support (Ubuntu 20.04 in this case)
FROM ubuntu:20.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --upgrade pip

# Install the CPU version of PyTorch and Hugging Face Transformers
RUN pip3 install torch torchvision torchaudio

# Install other necessary dependencies including YOLOv8, OpenCV, Flask, and missing packages
RUN pip3 install opencv-python-headless ultralytics transformers flask gunicorn \
    accelerate tiktoken verovio

# Set the working directory
WORKDIR /app

# Copy your application and models into the container
COPY . /app

# Expose the port on which the Flask app will run
EXPOSE 5000

# Run the Flask app using Gunicorn in production mode
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
