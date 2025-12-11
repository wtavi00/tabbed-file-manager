# Docker Setup for Python File Manager

This guide explains how to run the Python File Manager in a Docker container.

## Important Limitations

**GUI applications in Docker have significant limitations:**
- Requires X11 forwarding configuration
- May have display issues depending on your host OS
- Performance may be slower than running natively
- Not recommended for production use

**Recommendation:** For the best experience, run the file manager directly on your host system with `python main.py`.

