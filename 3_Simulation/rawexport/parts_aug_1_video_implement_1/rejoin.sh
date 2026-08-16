#!/usr/bin/env bash
# Automatically generated rejoin script
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT="../aug 1 video implement (1).mp4"
echo "🧩 Rejoining parts into: $OUT"
cat "$DIR"/aug_1_video_implement_1.part_* > "$OUT"
echo "✅ Done! Reassembled $OUT"
