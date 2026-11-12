#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

export PATH="/opt/homebrew/bin:$PATH"

echo "=========================================================="
echo "   NEXORA Order Agent - Enterprise Migration Video Studio  "
echo "   MNC Presentation & Zero-Error Technical Architecture   "
echo "=========================================================="
echo ""
echo "[1/3] Activating virtual environment..."
source "$DIR/venv/bin/activate"

echo "[2/3] Rendering 1080p Executive Presentation with Christopher Neural Voiceover..."
python "$DIR/backend/scripts/generate_migration_presentation_video.py"

echo "[3/3] Opening generated migration presentation in QuickTime Player..."
if [ -f "$DIR/nexora_migration_presentation_1080p.mp4" ]; then
    open "$DIR/nexora_migration_presentation_1080p.mp4"
fi

echo ""
echo "=========================================================="
echo " SUCCESS! Enterprise Migration Video ready."
echo " File: $DIR/nexora_migration_presentation_1080p.mp4"
echo " Desktop: /Users/mohammedumar/Desktop/NEXORA_Enterprise_Migration_Presentation.mp4"
echo " Web Stream: http://127.0.0.1:8000/demo-video.mp4"
echo "=========================================================="
