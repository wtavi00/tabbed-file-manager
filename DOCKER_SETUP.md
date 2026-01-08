# Docker Setup for Python File Manager

This guide explains how to run the Python File Manager in a Docker container.

## Important Limitations

**GUI applications in Docker have significant limitations:**
- Requires X11 forwarding configuration
- May have display issues depending on your host OS
- Performance may be slower than running natively
- Not recommended for production use

**Recommendation:** For the best experience, run the file manager directly on your host system with `python main.py`.

## Files Included

- `Dockerfile` - Container definition
- `docker-compose.yml` - Docker Compose configuration
- `requirements.txt` - Python dependencies

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed
- X11 server running (for GUI display)


## Setup Instructions

### Linux

1. **Allow X11 connections:**
   ```bash
   xhost +local:docker
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **When finished, restore X11 security:**
   ```bash
   xhost -local:docker
   ```
   
### macOS

   **Install XQuartz:**
   ```bash
   brew install --cask xquartz
   ```

   **Start XQuartz and configure:**
   - Open XQuartz
   - Go to Preferences > Security
   - Enable "Allow connections from network clients"
   - Restart XQuartz

   **Allow X11 connections:**
   ```bash
   xhost + 127.0.0.1
   ```
   **Set DISPLAY variable:**
   ```bash
   export DISPLAY=host.docker.internal:0
   ```
   **Build and run:**
   ```bash
   docker-compose up --build
   ```
