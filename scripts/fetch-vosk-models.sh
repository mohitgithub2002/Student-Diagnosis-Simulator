#!/usr/bin/env bash
# Download small Vosk speech models (Indian English, Hindi) for on-device speech-to-text.
# - The web app (vosk-browser) loads .tar.gz archives, so the official .zip files are repackaged.
# - The Android app installs the original .zip, checked against the SHA-256 in models/manifest.json.
# Hinglish has no model (its Roman script doesn't match the Hindi model's Devanagari output).
# Models stay out of git and are served from apps/web/public/models/ (/models/ on the web server).
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/apps/web/public/models"
mkdir -p "$DEST"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
MODELS=(vosk-model-small-en-in-0.4 vosk-model-small-hi-0.22)
for MODEL in "${MODELS[@]}"; do
  if [ -f "$DEST/$MODEL.zip" ] && [ -f "$DEST/$MODEL.tar.gz" ]; then echo "$MODEL already present"; continue; fi
  echo "Downloading $MODEL…"
  curl -fL "https://alphacephei.com/vosk/models/$MODEL.zip" -o "$TMP/$MODEL.zip"
  unzip -q "$TMP/$MODEL.zip" -d "$TMP"
  tar -czf "$DEST/$MODEL.tar.gz" -C "$TMP" "$MODEL"
  cp "$TMP/$MODEL.zip" "$DEST/$MODEL.zip"
  echo "Saved $DEST/$MODEL.tar.gz and $MODEL.zip"
done

# Manifest for the Android app: archive name, SHA-256 and size per model.
{
  echo "{"
  for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    SHA="$(sha256sum "$DEST/$MODEL.zip" | cut -d' ' -f1)"
    BYTES="$(stat -c %s "$DEST/$MODEL.zip")"
    SEP=","; [ "$i" -eq $((${#MODELS[@]} - 1)) ] && SEP=""
    echo "  \"$MODEL\": {\"zip\": \"$MODEL.zip\", \"sha256\": \"$SHA\", \"bytes\": $BYTES}$SEP"
  done
  echo "}"
} > "$DEST/manifest.json"
echo "Wrote $DEST/manifest.json"
