#!/bin/bash

# Script to download recordings from Render backend
# Run this regularly to backup recordings before Render restarts

BACKEND_URL="https://eri-tig-recorder.onrender.com"
OUTPUT_DIR="./downloaded_recordings"

echo "📥 Downloading recordings from Render backend..."
echo "Backend: $BACKEND_URL"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get stats
echo "📊 Getting stats..."
curl -s "$BACKEND_URL/stats" | python3 -m json.tool

echo ""
echo "⚠️ Note: Render's free tier has ephemeral storage."
echo "⚠️ Recordings are only available if Dropbox backup is configured."
echo ""
echo "To view recordings, check your Dropbox at:"
echo "https://www.dropbox.com/home/tigrigna_training_dataset"
echo ""
echo "✅ Make sure you added these to Render Environment Variables:"
echo "   - DROPBOX_ACCESS_TOKEN"
echo "   - DROPBOX_FOLDER_PATH=/tigrigna_training_dataset"
