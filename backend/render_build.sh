#!/usr/bin/env bash
set -e

echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1

echo "System dependencies installed successfully"
