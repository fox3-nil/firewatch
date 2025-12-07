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

echo "[1/6] Checking for virtual environment directory"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "No venv found. Creating one..."
    python3 -m venv "$VENV_DIR"
else
    echo "Existing venv detected."
fi

echo "[2/6] Activating virtual environment..."
#shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Python executable now: $(which python3)"

echo "[3/6] Updating apt..."
apt update

echo "[4/6] Installing system packages..."
apt install -y python3-pip python3-smbus i2c-tools libatlas-base-dev python3-pil libcamera-tools python3-libcamera

echo "[5/6] Upgrading pip..."
pip3 install --upgrade pip

echo "[6/6] Installing Python libraries..."
pip3 install \
    adafruit-blinka \
    adafruit-circuitpython-ahtx0 \
    adafruit-circuitpython-mlx90640 \
    smbus2 \
    getmac \


echo "=== Installation Complete! ==="
echo "All required libraries are installed."
echo ""
echo "To run FireWatch, enter: \"source FireWatch/bin/activate\" and then run main.py"
