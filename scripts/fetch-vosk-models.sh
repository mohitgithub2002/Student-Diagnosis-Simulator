#!/usr/bin/env bash
# Download small Vosk speech models (Indian English, Hindi) for on-device speech-to-text in the web app.
# vosk-browser loads .tar.gz archives, so the official .zip files are repackaged. Models stay out of git.
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/apps/web/public/models"
mkdir -p "$DEST"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
for MODEL in vosk-model-small-en-in-0.4 vosk-model-small-hi-0.22; do
  if [ -f "$DEST/$MODEL.tar.gz" ]; then echo "$MODEL already present"; continue; fi
  echo "Downloading $MODEL…"
  curl -fL "https://alphacephei.com/vosk/models/$MODEL.zip" -o "$TMP/$MODEL.zip"
  unzip -q "$TMP/$MODEL.zip" -d "$TMP"
  tar -czf "$DEST/$MODEL.tar.gz" -C "$TMP" "$MODEL"
  echo "Saved $DEST/$MODEL.tar.gz"
done
