#!/usr/bin/env bash
# ==============================================================================
# DEMGen Manim Slides Presentation Build & Present Script
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

QUALITY="${1:-m}" # l: 480p, m: 720p, h: 1080p, k: 4K

echo "======================================================="
echo "  DEMGen Presentation - Manim Slides"
echo "  Rendering quality: -$QUALITY"
echo "======================================================="

# Render scene
manim -q"$QUALITY" presentation.py Presentation

# Export to standalone HTML presentation (Reveal.js based)
echo ""
echo "--> Generating standalone HTML presentation..."
manim-slides convert Presentation presentation_slides.html

echo ""
echo "======================================================="
echo "  Render complete!"
echo ""
echo "  To present interactively in the terminal window:"
echo "    manim-slides present Presentation"
echo ""
echo "  To view the standalone HTML presentation in browser:"
echo "    open presentation_slides.html  (or xdg-open presentation_slides.html)"
echo "======================================================="
