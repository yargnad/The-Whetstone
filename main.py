"""
The Whetstone - Unified Application Entry Point
-----------------------------------------------
Run the TUI or Web Interface from a single command.

Usage:
    python main.py tui      # Launch the Terminal User Interface
    python main.py web      # Launch the Web API / Interface
"""
import sys
import os
import argparse
import subprocess
# import uvicorn (Moved to run_web)
from utils import is_ollama_running, launch_ollama_server

# Import applications
# We deliberately import inside functions if needed to avoid dependency overhead 
# if one mode doesn't need the other's heavy libs (though currently they share most).
# For now, top level imports are fine as they are in the same venv.

def verify_backend():
    if os.getenv("WHETSTONE_BACKEND", "ollama") == "ollama":
        if not is_ollama_running():
            launch_ollama_server()

def run_tui():
    try:
        from tui_app import WhetstoneTUI
    except ImportError as e:
        print(f"[!] Error loading TUI: {e}")
        print("    Ensure 'textual' is installed: pip install textual")
        return

    # Ensure backend
    verify_backend()
            
    # Run App
    app = WhetstoneTUI()
    app.run()

def run_web(host="0.0.0.0", port=8080, ssl_keyfile=None, ssl_certfile=None):
    try:
        import uvicorn
        from web_api import app
    except ImportError as e:
        print(f"[!] Error loading Web API: {e}")
        print("    Ensure 'uvicorn' and 'fastapi' are installed.")
        return
    
    # Ensure backend
    verify_backend()
            
    protocol = "https" if ssl_keyfile and ssl_certfile else "http"
    
    # Improve display for local binding
    display_host = host
    if host == "0.0.0.0":
        display_host = "localhost"
        
    print("\n" + "="*50)
    print(f"  THE WHETSTONE - Web Interface")
    print(f"  {protocol}://{display_host}:{port}")
    if protocol == "https":
        print(f"  SSL Enabled: {os.path.basename(ssl_certfile)}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info", ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)

def main():
    parser = argparse.ArgumentParser(description="The Whetstone Application Launcher")
    subparsers = parser.add_subparsers(dest="mode", help="Mode to run")
    
    # TUI Mode
    tui_parser = subparsers.add_parser("tui", help="Run the Terminal User Interface")
    
    # Web Mode
    web_parser = subparsers.add_parser("web", help="Run the Web API/GUI Server")
    web_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    web_parser.add_argument("--port", type=int, default=8080, help="Bind port")
    web_parser.add_argument("--cert", help="Path to SSL certificate (.crt)")
    web_parser.add_argument("--key", help="Path to SSL private key (.key)")

    # Legacy CLI Mode
    cli_parser = subparsers.add_parser("cli", help="Run the Legacy Interactive CLI")

    args = parser.parse_args()
    
    if args.mode == "tui":
        run_tui()
    elif args.mode == "web":
        # Auto-detect Tailscale certs if not provided
        cert_file = args.cert
        key_file = args.key
        
        if not cert_file or not key_file:
            # Look for *.ts.net.crt/key in current dir
            import glob
            ts_certs = glob.glob("*.ts.net.crt")
            if ts_certs:
                # Use the first one found
                candidate_cert = ts_certs[0]
                candidate_key = candidate_cert.replace(".crt", ".key")
                if os.path.exists(candidate_key):
                    print(f"[Main] Detected Tailscale certificate: {candidate_cert}")
                    if not cert_file: cert_file = candidate_cert
                    if not key_file: key_file = candidate_key

        run_web(host=args.host, port=args.port, ssl_keyfile=key_file, ssl_certfile=cert_file)
    elif args.mode == "cli":
        from philosopher_app import run_cli_mode
        # Ensure backend
        verify_backend()
        run_cli_mode()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
