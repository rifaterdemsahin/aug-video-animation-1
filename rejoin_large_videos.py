#!/usr/bin/env python3
"""
🧩 Video Rejointer for GitHub
=============================
Scans `3_Simulation/rawexport/` (or any target folder) for split video parts
(`parts_*/split_manifest.json`), verifies SHA256 checksums, and reassembles
the original full MP4 file bit-for-bit.
"""

import os
import sys
import glob
import json
import hashlib
import argparse

DEFAULT_DIR = "3_Simulation/rawexport"

def calculate_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def rejoin_manifest(manifest_path: str) -> bool:
    parts_dir = os.path.dirname(manifest_path)
    parent_dir = os.path.dirname(parts_dir)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    original_file = manifest.get("original_file", "reassembled_video.mp4")
    original_sha = manifest.get("original_sha256", "")
    parts = manifest.get("parts", [])

    out_path = os.path.join(parent_dir, original_file)
    print(f"🧩 Rejoining {len(parts)} parts -> {out_path}...")

    # Validate parts exist
    for p in parts:
        part_file = os.path.join(parts_dir, p["filename"])
        if not os.path.exists(part_file):
            print(f"❌ Missing part: {part_file}")
            return False

    with open(out_path, "wb") as outfile:
        for p in parts:
            part_file = os.path.join(parts_dir, p["filename"])
            with open(part_file, "rb") as infile:
                while chunk := infile.read(1024 * 1024):
                    outfile.write(chunk)
            print(f"   ✓ Joined: {p['filename']}")

    # Verify SHA256
    print("🔍 Verifying reassembled file checksum...")
    reassembled_sha = calculate_sha256(out_path)
    if original_sha and reassembled_sha != original_sha:
        print(f"❌ Checksum mismatch!\n   Expected: {original_sha}\n   Got:      {reassembled_sha}")
        return False

    rejoined_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"✅ Reassembly Verified! {original_file} ({rejoined_mb:.2f} MB)")
    print(f"   SHA256: {reassembled_sha}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Rejoin split video parts into full original MP4.")
    parser.add_argument("--dir", type=str, default=DEFAULT_DIR, help="Directory to scan for parts_* folders.")
    args = parser.parse_args()

    manifests = glob.glob(os.path.join(args.dir, "parts_*", "split_manifest.json")) + glob.glob(os.path.join(args.dir, "**", "split_manifest.json"), recursive=True)

    if not manifests:
        print(f"ℹ️ No split parts manifests found in {args.dir}/")
        return

    for mf in sorted(set(manifests)):
        rejoin_manifest(mf)

if __name__ == "__main__":
    main()
