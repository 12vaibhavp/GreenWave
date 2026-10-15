#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "===> Upgrading pip..."
pip install --upgrade pip

echo "===> Installing CPU-only PyTorch (optimized for cloud deployment)..."
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo "===> Installing application requirements..."
pip install --no-cache-dir -r requirements.txt

echo "===> Build completed successfully!"
