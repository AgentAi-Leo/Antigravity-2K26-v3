#!/bin/bash

# show_result.sh - Surfaces skill output in the Antigravity UI
# Usage: ./show_result.sh <pdf_path>

PDF_PATH="$1"
ARTIFACT_DIR="/Users/jb3/.gemini/antigravity/brain/53e5fe71-2f4f-43e9-8302-cf84ffeb6a4f"

if [ -z "$PDF_PATH" ]; then
    echo "Usage: ./show_result.sh <pdf_path>"
    exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
    echo "Error: File not found: $PDF_PATH"
    exit 1
fi

# We copy to the user's Downloads folder so they always have easy access to the result
FILENAME=$(basename "$PDF_PATH")
DOWNLOADS_DIR="$HOME/Downloads"
DEST="$DOWNLOADS_DIR/$FILENAME"

cp "$PDF_PATH" "$DEST"
echo "✅ Result saved to: $DEST"

# macOS native command to instantly pop-up the file
if command -v open > /dev/null; then
    echo "👀 Opening $FILENAME on screen..."
    open "$DEST"
fi
