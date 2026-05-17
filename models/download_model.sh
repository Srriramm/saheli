#!/usr/bin/env bash
# download_model.sh — Pull Gemma 4 E4B GGUF weights for offline inference.
#
# Usage:
#   chmod +x models/download_model.sh
#   ./models/download_model.sh
#
# Requirements: curl (or wget), ~2.5 GB free disk space.
# The downloaded GGUF is placed at ./models/gemma-4-e4b-q4_k_m.gguf
# which matches MODEL_PATH in config/settings.py.

set -euo pipefail

MODEL_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_FILE="gemma-4-E4B-IT-Q4_K_M.gguf"
MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"

# Saheli fine-tuned model (LoRA-trained on WHO ANC maternal health data)
HF_REPO="sriramarivazhagan/saheli-gemma4-maternal-health-GGUF"
HF_FILE="saheli-gemma4-E4B-maternal-health-Q4_K_M.gguf"
HF_URL="https://huggingface.co/${HF_REPO}/resolve/main/${HF_FILE}"

# Multimodal projector from base model repo (for image/photo support)
HF_MMPROJ_FILE="gemma-4-E4B-IT-mmproj-f16.gguf"
HF_MMPROJ_URL="https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/${HF_MMPROJ_FILE}"
MMPROJ_PATH="${MODEL_DIR}/gemma-4-E4B-IT-mmproj-f16.gguf"

echo "========================================"
echo "  Saheli — Gemma 4 E4B Model Download"
echo "========================================"
echo "Base model : ${MODEL_PATH}"
echo "mmproj     : ${MMPROJ_PATH}"
echo ""

mkdir -p "${MODEL_DIR}"

_download() {
  local url="$1"
  local dest="$2"
  if [ -f "${dest}" ]; then
    echo "Already exists: ${dest}. Skipping."
    return 0
  fi
  if command -v curl &>/dev/null; then
    curl -L --progress-bar -o "${dest}" "${url}"
  elif command -v wget &>/dev/null; then
    wget --show-progress -O "${dest}" "${url}"
  else
    echo "ERROR: Neither curl nor wget found. Install one and retry."
    exit 1
  fi
}

echo "--- Downloading base GGUF ---"
_download "${HF_URL}" "${MODEL_PATH}"

echo ""
echo "--- Downloading multimodal projector (mmproj) ---"
echo "    Required for image/photo analysis support."
_download "${HF_MMPROJ_URL}" "${MMPROJ_PATH}"

echo ""
echo "Download complete."
echo "Base model : $(du -sh "${MODEL_PATH}" 2>/dev/null | cut -f1)"
echo "mmproj     : $(du -sh "${MMPROJ_PATH}" 2>/dev/null | cut -f1)"
echo ""
echo "Run 'python run.py' to start Saheli."
