#!/bin/bash

set -e

echo "=== FireWatch Library Installer ==="

# Must be run with sudo
if [[ $EUID -eq 0 ]]; then
    echo "[WARNING]: Do not run this script as root or with sudo!"
    echo "Run as: ./firewatch_libs.sh"
    exit 1
fi

VENV_DIR="FireWatch_VENV"

echo "[1/7] Checking for virtual environment directory"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "No venv found. Creating one..."
    python3 -m venv "$VENV_DIR"
else
    echo "Existing venv detected."
fi

echo "[2/7] Activating virtual environment..."
#shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Python executable now: $(which python3)"

echo "[3/7] Updating apt..."
sudo apt update

echo "[4/7] Installing system packages..."
sudo apt install -y python3-pip python3-smbus i2c-tools python3-pil libcamera-tools python3-libcamera

echo "[5/7] Upgrading pip..."
pip3 install --upgrade pip

echo "[6/7] Installing Python libraries..."
pip3 install \
    adafruit-blinka \
    adafruit-circuitpython-ahtx0 \
    adafruit-circuitpython-mlx90640 \
    smbus2 \
    getmac \

echo "[7/7] Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/firewatch-debug.service"

sudo bash -c "cat > $SERVICE_FILE" << 'EOF'

[Unit]
Description=FireWatch Sensor Debugging Service
After=network.target

[Service]
WorkingDirectory=/home/firewatch/firewatch
Environment="PATH=/home/firewatch/firewatch/FireWatch_VENV/bin"
ExecStart=/home/firewatch/firewatch/FireWatch_VENV/bin/python /home/firewatch/firewatch/serialdebug.py

# Auto-restart on failure
Restart=always
RestartSec=3

User=firewatch
Group=firewatch

# Systemd logs instead of TTY
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable firewatch-debug.service

echo "Starting service..."
sudo systemctl start firewatch-debug.service

echo "Serial Debug service installed and running!"

echo "=== Installation Complete! ==="
echo "All required libraries are installed."
echo ""
echo "To run FireWatch, enter: \"source FireWatch/bin/activate\" and then run main.py"
