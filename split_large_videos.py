#!/usr/bin/env python3
"""
📦 Video Splitter for GitHub (24 MB Chunks)
=============================================
Splits large raw video files (> 24MB) into 24 MB binary chunks so they can be
pushed to GitHub without triggering GitHub's 50MB/100MB file limits.

Also generates:
- `rejoin_large_videos.py` (Universal cross-platform rejointer)
- Shell `rejoin.sh` script
- `split_manifest.json` (SHA256 checksum verification)
"""

import os
import sys
import glob
import json
import hashlib
import argparse

CHUNK_SIZE_MB = 24
CHUNK_SIZE_BYTES = CHUNK_SIZE_MB * 1024 * 1024  # 25,165,824 bytes
DEFAULT_DIR = "3_Simulation/rawexport"

def calculate_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def sanitize_name(filename: str) -> str:
    return filename.replace(" ", "_").replace("(", "").replace(")", "").replace(".mp4", "").replace(".mov", "")

def split_file(filepath: str, output_base_dir: str = None, chunk_size: int = CHUNK_SIZE_BYTES):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    file_size = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    file_size_mb = file_size / (1024 * 1024)

    print(f"🎬 Processing: {filename} ({file_size_mb:.2f} MB)")

    if file_size <= chunk_size:
        print(f"ℹ️ File is already under {CHUNK_SIZE_MB}MB ({file_size_mb:.2f} MB). No splitting required.")
        return True

    parent_dir = os.path.dirname(filepath)
    sanitized = sanitize_name(filename)
    parts_dir = os.path.join(parent_dir, f"parts_{sanitized}")
    os.makedirs(parts_dir, exist_ok=True)

    print(f"📦 Splitting into {CHUNK_SIZE_MB} MB chunks -> {parts_dir}/")

    print("🔍 Calculating SHA256 checksum...")
    original_sha256 = calculate_sha256(filepath)
    print(f"   SHA256: {original_sha256}")

    part_num = 1
    part_files = []

    with open(filepath, "rb") as infile:
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                break
            
            part_name = f"{sanitized}.part_{part_num:03d}"
            part_path = os.path.join(parts_dir, part_name)
            
            with open(part_path, "wb") as outfile:
                outfile.write(chunk)
            
            part_size_mb = len(chunk) / (1024 * 1024)
            part_sha = hashlib.sha256(chunk).hexdigest()
            print(f"   ✅ Created: {part_name} ({part_size_mb:.2f} MB)")
            
            part_files.append({
                "part_number": part_num,
                "filename": part_name,
                "size_bytes": len(chunk),
                "size_mb": round(part_size_mb, 2),
                "sha256": part_sha
            })
            part_num += 1

    # Write Manifest
    manifest = {
        "original_file": filename,
        "original_size_bytes": file_size,
        "original_size_mb": round(file_size_mb, 2),
        "original_sha256": original_sha256,
        "chunk_size_mb": CHUNK_SIZE_MB,
        "total_parts": len(part_files),
        "parts": part_files
    }
    
    manifest_path = os.path.join(parts_dir, "split_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    # Write Rejoin Shell Script
    rejoin_sh_path = os.path.join(parts_dir, "rejoin.sh")
    part_wildcard = f"{sanitized}.part_*"
    with open(rejoin_sh_path, "w", encoding="utf-8") as sf:
        sf.write(f"""#!/usr/bin/env bash
# Automatically generated rejoin script
set -e
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
OUT="../{filename}"
echo "🧩 Rejoining parts into: $OUT"
cat "$DIR"/{part_wildcard} > "$OUT"
echo "✅ Done! Reassembled $OUT"
""")
    os.chmod(rejoin_sh_path, 0o755)

    print(f"\n🎉 Successfully split into {len(part_files)} pieces!")
    print(f"   • Folder: {parts_dir}/")
    print(f"   • Manifest: {manifest_path}")
    print(f"   • Rejoin helper: {rejoin_sh_path} or `python3 rejoin_large_videos.py`")
    return True

def main():
    parser = argparse.ArgumentParser(description="Split large video files into 24MB pieces for GitHub.")
    parser.add_argument("--file", type=str, default="", help="Specific video file to split.")
    parser.add_argument("--dir", type=str, default=DEFAULT_DIR, help="Directory to scan for large videos.")
    parser.add_argument("--chunk-mb", type=int, default=CHUNK_SIZE_MB, help="Chunk size in MB (default: 24).")
    args = parser.parse_args()

    chunk_bytes = args.chunk_mb * 1024 * 1024

    if args.file:
        split_file(args.file, chunk_size=chunk_bytes)
        return

    # Scan directory for videos > 24MB
    video_files = glob.glob(os.path.join(args.dir, "*.mp4")) + glob.glob(os.path.join(args.dir, "*.mov"))
    large_files = [f for f in video_files if os.path.getsize(f) > chunk_bytes]

    if not large_files:
        print(f"ℹ️ No videos > {args.chunk_mb}MB found in {args.dir}/")
        if video_files:
            print(f"   Found smaller videos: {[os.path.basename(v) for v in video_files]}")
        return

    for vf in large_files:
        split_file(vf, chunk_size=chunk_bytes)

if __name__ == "__main__":
    main()
