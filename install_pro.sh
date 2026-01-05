#!/bin/bash
# The Whetstone - Pro Edition Installation Script
# Target: Radxa Rock 5B+ with Armbian/Ubuntu 22.04+
# 
# Usage: curl -fsSL https://raw.githubusercontent.com/yargnad/The-Whetstone/main/install_pro.sh | bash

set -e

WHETSTONE_DIR="${HOME}/The-Whetstone"
MODEL="${WHETSTONE_MODEL:-qwen3:14b}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║               The Whetstone - Pro Edition                    ║"
echo "║                    Installation Script                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running on ARM64 (Rock 5B+)
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    echo "[WARN] This script is designed for ARM64 (aarch64). Detected: $ARCH"
    echo "       Proceeding anyway..."
fi

# 1. System dependencies
echo "[1/6] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    git curl wget \
    ffmpeg \
    libffi-dev \
    cmake

# 2. Backend Selection
echo "[2/6] Selecting inference backend..."
echo ""
echo "  Choose your backend:"
echo "    1) Ollama (recommended, easier setup)"
echo "    2) llama.cpp (direct inference, no server required)"
echo ""
read -p "  Enter choice [1]: " BACKEND_CHOICE
BACKEND_CHOICE=${BACKEND_CHOICE:-1}

if [[ "$BACKEND_CHOICE" == "2" ]]; then
    BACKEND="llamacpp"
    echo "       Selected: llama.cpp"
else
    BACKEND="ollama"
    echo "       Selected: Ollama"
    
    # Install Ollama
    if command -v ollama &> /dev/null; then
        echo "       Ollama already installed, skipping..."
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    # 3. Pull the model
    echo "[3/6] Pulling ${MODEL}... (this may take a while)"
    ollama pull "${MODEL}"
fi

# 4. Clone or update The Whetstone
echo "[4/6] Setting up The Whetstone..."
if [[ -d "$WHETSTONE_DIR" ]]; then
    echo "       Directory exists, pulling latest..."
    cd "$WHETSTONE_DIR"
    git pull || echo "       Not a git repo or no remote, continuing..."
else
    echo "       Cloning repository..."
    git clone https://github.com/yargnad/The-Whetstone.git "$WHETSTONE_DIR"
    cd "$WHETSTONE_DIR"
fi

# 5. Python virtual environment
echo "[5/6] Setting up Python environment..."
if [[ ! -d "${WHETSTONE_DIR}/venv" ]]; then
    python3 -m venv "${WHETSTONE_DIR}/venv"
fi
source "${WHETSTONE_DIR}/venv/bin/activate"
pip install --upgrade pip
pip install -r "${WHETSTONE_DIR}/requirements.txt"

# Install llama-cpp-python if that backend was selected
if [[ "$BACKEND" == "llamacpp" ]]; then
    echo "       Installing llama-cpp-python (may take several minutes)..."
    sudo apt-get install -y libopenblas-dev
    CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python
    
    # Prompt for model path
    echo ""
    echo "  llama.cpp requires a GGUF model file."
    echo "  Download one from: https://huggingface.co/Qwen/Qwen3-14B-GGUF"
    read -p "  Enter path to your .gguf model file: " MODEL_PATH
    export WHETSTONE_MODEL_PATH="$MODEL_PATH"
fi

# 6. Create systemd service (optional)
echo "[6/6] Creating systemd service..."
SYSTEMD_SERVICE="/etc/systemd/system/whetstone.service"
if [[ ! -f "$SYSTEMD_SERVICE" ]]; then
    sudo tee "$SYSTEMD_SERVICE" > /dev/null << EOF
[Unit]
Description=The Whetstone - Socratic AI Companion
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WHETSTONE_DIR}
Environment="WHETSTONE_BACKEND=${BACKEND}"
Environment="WHETSTONE_MODEL=${MODEL}"
Environment="WHETSTONE_MODEL_PATH=${WHETSTONE_MODEL_PATH:-}"
Environment="OLLAMA_CONTEXT_LENGTH=32768"
ExecStart=${WHETSTONE_DIR}/venv/bin/python3 ${WHETSTONE_DIR}/philosopher_app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    echo "       Service created. Enable with: sudo systemctl enable whetstone"
else
    echo "       Service already exists, skipping..."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   Installation Complete!                     ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ To run manually:                                             ║"
echo "║   cd ${WHETSTONE_DIR}                                        ║"
echo "║   source venv/bin/activate                                   ║"
echo "║   python philosopher_app.py                                  ║"
echo "║                                                              ║"
echo "║ To run as service:                                           ║"
echo "║   sudo systemctl enable --now whetstone                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
