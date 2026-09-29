"""
EduGenie Launch Script
Starts the FastAPI application with Uvicorn.
"""
import sys
import socket
import argparse
import uvicorn

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a given port is already in use or restricted."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def find_available_port(preferred_port: int = 8000, host: str = "127.0.0.1") -> int:
    """Find an available port starting from preferred_port."""
    for port in [preferred_port, 8001, 8080, 8888, 5000]:
        if not is_port_in_use(port, host):
            return port
    return preferred_port

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EduGenie AI Learning Assistant")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (slower, for development)")
    args, unknown = parser.parse_known_args()

    port = args.port
    if is_port_in_use(port, args.host):
        alt_port = find_available_port(port + 1, args.host)
        print(f"[!] Warning: Port {port} is currently in use or restricted.")
        print(f"[*] Automatically switching to available port: {alt_port}")
        port = alt_port

    print("=" * 60)
    print("  EduGenie - AI Learning Assistant")
    print("  Powered by Ollama (qwen3:8b) — 100% Local AI")
    print("  'Learn Smarter. Understand Faster. Grow Better.'")
    print("=" * 60)
    print(f"Starting local server at http://{args.host}:{port} ...")
    print(f"Web Application URL: http://localhost:{port}")
    print(f"Interactive API Docs: http://localhost:{port}/docs")
    print("Press Ctrl+C to stop the server.\n")

    uvicorn.run("backend.main:app", host=args.host, port=port, reload=args.reload)

