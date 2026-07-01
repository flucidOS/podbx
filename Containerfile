# FlucidOS Base Workspace Image
# We use the slim version of Debian stable to save disk space
FROM docker.io/library/debian:stable-slim

# Set environment variables for non-interactive apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Update and install the "Just Works" toolkit for students and developers.
# This prevents them from needing to install basic utilities every time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    curl \
    wget \
    git \
    nano \
    vim \
    unzip \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    bash-completion \
    ca-certificates \
    man-db \
    && rm -rf /var/lib/apt/lists/*

# Distrobox handles user creation and mapping automatically at runtime,
# so we do not need to define a custom user here. We just provide the clean, enriched base.
