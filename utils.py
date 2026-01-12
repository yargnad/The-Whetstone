import os
import sys
import socket
import subprocess
import time

def is_ollama_running(host="127.0.0.1", port=11434):
    """Check if Ollama server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

def launch_ollama_server():
    """Launch Ollama server if not running."""
    print("[INFO] Ollama server not detected. Launching 'ollama serve' with 16k context window...")
    env = os.environ.copy()
    env["OLLAMA_CONTEXT_LENGTH"] = "16384"
    
    stdout_target = subprocess.DEVNULL
    stderr_target = subprocess.DEVNULL
    
    if sys.platform.startswith("win"):
        # Windows: Detached process
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(["ollama", "serve"], creationflags=DETACHED_PROCESS, stdout=stdout_target, stderr=stderr_target, env=env)
    else:
        # Linux/Mac: Start new session
        subprocess.Popen(["ollama", "serve"], start_new_session=True, stdout=stdout_target, stderr=stderr_target, env=env)
    
    # Wait for startup
    for _ in range(30):
        if is_ollama_running():
            print("[INFO] Ollama server is now running.")
            return
        time.sleep(1)
    
    print("[ERROR] Ollama server did not start within 30 seconds.")
