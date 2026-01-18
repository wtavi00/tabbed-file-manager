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

### Windows

Running GUI applications in Docker on Windows is complex and not recommended. Instead:

**Option 1: Use WSL2 (Recommended)**
1. Install WSL2 with Ubuntu
2. Install VcXsrv or X410 for X11
3. Follow Linux instructions within WSL2

**Option 2: Run Natively (Best)**
```bash
pip install Pillow
python main.py
```

## Manual Docker Commands

If you prefer not to use docker-compose:

### Build the image:
```bash
docker build -t python-file-manager .
```

### Run the container (Linux):
```bash
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/data \
  python-file-manager
```

### Run the container (macOS):
```bash
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/data \
  python-file-manager
```

## Directory Structure

```
python-file-manager/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py
├── README.md
├── DOCKER_SETUP.md
└── data/              # Mounted volume for file operations
```

## Troubleshooting

### Error: "cannot open display"

**Linux:**
```bash
xhost +local:docker
echo $DISPLAY  # Should show something like :0 or :1
```

**macOS:**
- Ensure XQuartz is running
- Check DISPLAY variable: `echo $DISPLAY`
- Try: `export DISPLAY=host.docker.internal:0`

### GUI appears but is very slow

This is normal for X11 forwarding. Consider running natively for better performance.

### Permission denied errors

```bash
# Give Docker access to X11
xhost +local:docker

# Or for specific user (more secure)
xhost +SI:localuser:$(whoami)
```

### Container can't access files

Check volume mounts in `docker-compose.yml`:
```yaml
volumes:
  - ./data:/data          # Current directory's data folder
  - ${HOME}:/host-home    # Your home directory
```
