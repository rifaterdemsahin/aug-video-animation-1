#!/usr/bin/env python3
"""
🎬 1-Second Frame Extractor & Visual AI Voiceover Rewrite Engine
================================================================
Workflow:
1. Export raw video draft (with scratch voiceover) from Canva / DaVinci.
2. Drop the .mp4 into `3_Simulation/rawexport/`.
3. Run this script:
     python3 extract_and_rewrite_vo.py
4. Script extracts 1 screenshot per second into `3_Simulation/rawexport/screenshots/`.
5. Maps each 1-second frame to its corresponding Scene & Shot from the project script.
6. Generates AI-suggested voiceover variations directly from what is visible on screen.
7. Produces:
   - `3_Simulation/rawexport/voiceover_rewrite_workbench.md` (Markdown editor)
   - `3_Simulation/rawexport/voiceover_inspector.html` (Interactive visual scrubbing UI)
   - `3_Simulation/rawexport/frames_manifest.json` (Structured metadata)
"""

import os
import sys
import json
import glob
import subprocess
import argparse
from datetime import datetime

# Default paths
DEFAULT_INPUT_DIR = "3_Simulation/rawexport"
DEFAULT_OUTPUT_DIR = "3_Simulation/rawexport/screenshots"
DEFAULT_MD_DOC = "3_Simulation/rawexport/voiceover_rewrite_workbench.md"
DEFAULT_HTML_DOC = "3_Simulation/rawexport/voiceover_inspector.html"
DEFAULT_MANIFEST = "3_Simulation/rawexport/frames_manifest.json"

# Comprehensive Master Beats (Mapped across all 200 seconds: 00:00 to 03:20)
MASTER_BEATS = [
    # Scene 1: Hook & Problem Setup (0:00 - 0:18)
    {"start": 0, "end": 4, "scene": 1, "stage": "01", "name": "Hook & Problem Setup", "beat": "Drowning in Notes", "visual": "Dark workspace with glowing vault icon swirled by chaotic notes.", "base_vo": "I was drowning in 46,000 notes across Obsidian.", "ai_punchy": "46,000 Obsidian notes. Total digital chaos.", "ai_strategic": "I had accumulated over 46,000 notes with zero structure.", "ai_conversational": "Ever felt completely buried under your own Obsidian notes?"},
    {"start": 4, "end": 8, "scene": 1, "stage": "01", "name": "Hook & Problem Setup", "beat": "Digital Haystack", "visual": "46,000 note icons swirling into a digital vortex with search timeouts.", "base_vo": "Every search felt like looking for a needle in a digital haystack.", "ai_punchy": "Every search was a needle in a digital haystack.", "ai_strategic": "Unstructured search queries produced massive latency and noise.", "ai_conversational": "Searching for anything felt like looking for a needle in a haystack."},
    {"start": 8, "end": 13, "scene": 1, "stage": "01", "name": "Hook & Problem Setup", "beat": "The Root Cause", "visual": "Glitch red distortion on search bar with flashing red-X alert.", "base_vo": "And then I realized—the problem wasn't the number of notes.", "ai_punchy": "The problem wasn't the note count.", "ai_strategic": "The failure was architectural, not a volume limitation.", "ai_conversational": "And then it hit me: the problem wasn't having too many notes."},
    {"start": 13, "end": 19, "scene": 1, "stage": "01", "name": "Hook & Problem Setup", "beat": "Notes Working For You", "visual": "Camera zooms into locked vault core with red accent transition.", "base_vo": "It was that they weren't working for me.", "ai_punchy": "They just weren't working for me.", "ai_strategic": "Static notes generate zero leverage without active synthesis.", "ai_conversational": "It was that my notes simply weren't working for me."},

    # Scene 2: The Realization Moment (0:19 - 0:48)
    {"start": 19, "end": 24, "scene": 2, "stage": "02", "name": "The Realization Moment", "beat": "Engineering The Breakthrough", "visual": "Vault flashes gold as cybernetic graph network connects active nodes.", "base_vo": "So I engineered something different: an AI-native knowledge engine.", "ai_punchy": "So I built an AI-native second brain.", "ai_strategic": "I engineered a deterministic, machine-readable graph topology.", "ai_conversational": "So I engineered something new: an AI-native knowledge engine."},
    {"start": 24, "end": 30, "scene": 2, "stage": "02", "name": "The Realization Moment", "beat": "No More Manual Digging", "visual": "Red chaos nodes snap cleanly into synchronized cyan clusters.", "base_vo": "No more chaos. No more manual digging.", "ai_punchy": "No more manual digging. No more chaos.", "ai_strategic": "Manual folder hierarchies are completely eliminated.", "ai_conversational": "No more endless digging or messy folder searching."},
    {"start": 30, "end": 37, "scene": 2, "stage": "02", "name": "The Realization Moment", "beat": "Autonomous Agent Queries", "visual": "Dual agent cursors query, synthesize, and tag markdown files live.", "base_vo": "Instead, AI agents query, synthesize, and update my entire vault.", "ai_punchy": "AI agents query and synthesize everything automatically.", "ai_strategic": "Autonomous LLM agents continuously index and summarize knowledge.", "ai_conversational": "Now AI agents query and synthesize all my notes automatically."},
    {"start": 37, "end": 43, "scene": 2, "stage": "02", "name": "The Realization Moment", "beat": "Automatic Background Sync", "visual": "Automated sync status bar reaches 100% with gold checkmark.", "base_vo": "Everything updates automatically in the background.", "ai_punchy": "Everything updates silently while you sleep.", "ai_strategic": "Background workers ensure eventual consistency across all storage nodes.", "ai_conversational": "It all updates automatically in the background while I work."},
    {"start": 43, "end": 49, "scene": 2, "stage": "02", "name": "The Realization Moment", "beat": "AI Certification Blueprint", "visual": "Claude Certified Architect badge and exam readiness blueprint glow.", "base_vo": "And it prepares you for modern AI certifications like Claude Architect.", "ai_punchy": "Prepping you for top AI certifications like Claude Architect.", "ai_strategic": "Designed around the Claude Certified Architect Professional competency model.", "ai_conversational": "Plus it's built to prep you for top AI certs like Claude Architect."},

    # Scene 3: P.A.R.A. Method Framework (0:49 - 1:24)
    {"start": 49, "end": 54, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "Four Deterministic Zones", "visual": "Screen splits into 4 clean colored zone containers (Projects, Areas, Resources, Archive).", "base_vo": "The foundation is the P.A.R.A. method—four zones AI understands instantly.", "ai_punchy": "The backbone is P.A.R.A: four clean AI zones.", "ai_strategic": "P.A.R.A establishes deterministic boundaries for LLM context retrieval.", "ai_conversational": "The foundation is simple: four zones that AI understands instantly."},
    {"start": 54, "end": 60, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "Projects Zone (Red)", "visual": "Red container #e74c3c populating active tasks and sprint deadlines.", "base_vo": "Projects: short-term efforts with strict deadlines.", "ai_punchy": "Projects: active work with deadlines.", "ai_strategic": "Projects zone houses time-bounded execution objectives.", "ai_conversational": "Projects are your short-term goals with clear deadlines."},
    {"start": 60, "end": 66, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "Areas Zone (Blue)", "visual": "Blue container #3498db with systems, infrastructure, and ops records.", "base_vo": "Areas: long-term responsibilities you own continuously.", "ai_punchy": "Areas: permanent responsibilities you own.", "ai_strategic": "Areas zone manages continuous operational domain standards.", "ai_conversational": "Areas are ongoing responsibilities you manage every day."},
    {"start": 66, "end": 72, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "Resources Zone (Green)", "visual": "Green container #27ae60 with study material, research, and prompt templates.", "base_vo": "Resources: reference guides and topics of interest.", "ai_punchy": "Resources: curated references and research.", "ai_strategic": "Resources contain reusable prompt engineering and reference artifacts.", "ai_conversational": "Resources are your reference guides, cheat sheets, and research."},
    {"start": 72, "end": 78, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "Archive Zone (Gray)", "visual": "Gray container #95a5a6 with historical records indexed for fast retrieval.", "base_vo": "And Archive: everything inactive, perfectly indexed.", "ai_punchy": "Archive: inactive history, perfectly indexed.", "ai_strategic": "Archive provides cold storage with deterministic semantic indexing.", "ai_conversational": "And Archive holds past projects, indexed so you never lose context."},
    {"start": 78, "end": 85, "scene": 3, "stage": "03", "name": "P.A.R.A. Method Framework", "beat": "100x AI Speed Multiplier", "visual": "AI search benchmark radar graph shows 100x retrieval acceleration.", "base_vo": "AI agents navigate structured vaults 100x faster than messy folders.", "ai_punchy": "AI navigates clean structure 100x faster.", "ai_strategic": "Structured taxonomy cuts vector search latency by 99%.", "ai_conversational": "Clean structure means your AI agents find answers in seconds."},

    # Scene 4: The Engine: Dual-Agent System (1:25 - 1:58)
    {"start": 85, "end": 90, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "The Local Orchestration Rig", "visual": "Terminal dashboard boots at localhost:8899 with dual agent avatars.", "base_vo": "Then comes the engine: a local dual-agent orchestration rig.", "ai_punchy": "The engine: a local dual-agent orchestration rig.", "ai_strategic": "A resilient multi-agent architecture executing locally.", "ai_conversational": "Here is the engine: a local dual-agent rig running on your machine."},
    {"start": 90, "end": 96, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "Gemini Gold & Claude Blue", "visual": "Gemini Gold and Claude Blue avatars exchange structured JSON payloads.", "base_vo": "Running Gemini and Claude in parallel tandem.", "ai_punchy": "Gemini Gold and Claude Blue working in tandem.", "ai_strategic": "Dual frontier models operate concurrently for verification and synthesis.", "ai_conversational": "Gemini and Claude work together in real-time tandem."},
    {"start": 96, "end": 102, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "Background Autonomous Work", "visual": "Background workers sync data streams silently while user writes code.", "base_vo": "Running silently in the background while you focus on work.", "ai_punchy": "Running in the background while you build.", "ai_strategic": "Asynchronous event loops handle background maintenance jobs.", "ai_conversational": "They run silently in the background while you focus on shipping."},
    {"start": 102, "end": 108, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "Multi-Cloud Synchronization", "visual": "Tri-directional sync streams to GitHub, Google Drive, and Proxmox icons.", "base_vo": "Syncing across GitHub, Google Drive, and Proxmox.", "ai_punchy": "Syncing across GitHub, Drive, and Proxmox.", "ai_strategic": "Automated pipelines replicate state across multi-cloud infrastructure.", "ai_conversational": "Syncing all your files across GitHub, Drive, and Proxmox servers."},
    {"start": 108, "end": 114, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "Changelogs & Maintenance", "visual": "Automated git commit diffs, vault changelogs, and audit logs render live.", "base_vo": "Generating changelogs and maintaining folder integrity.", "ai_punchy": "Writing changelogs and keeping structures clean.", "ai_strategic": "Autonomous auditing guarantees zero drift across documentation repositories.", "ai_conversational": "Generating clean changelogs and keeping your structure spotless."},
    {"start": 114, "end": 119, "scene": 4, "stage": "04", "name": "The Engine: Dual-Agent System", "beat": "Execution Over Busywork", "visual": "Productivity chart spikes upward as manual busywork drops to zero.", "base_vo": "You focus on execution. They handle the busywork.", "ai_punchy": "You execute. They handle the busywork.", "ai_strategic": "Decouples high-leverage engineering from repetitive clerical tasks.", "ai_conversational": "You focus on high-impact work—they handle all the busywork."},

    # Scene 5: The 4-Step Workflow (1:59 - 2:32)
    {"start": 119, "end": 124, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Applied Knowledge Principle", "visual": "4-step conveyor assembly line appears with vibrant colored boxes.", "base_vo": "Raw knowledge isn't power—applied knowledge is.", "ai_punchy": "Raw knowledge isn't power—applied knowledge is.", "ai_strategic": "Information retrieval without production output yields zero value.", "ai_conversational": "Raw knowledge isn't power—only applied knowledge is."},
    {"start": 124, "end": 129, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Step 1: Tell (Obsidian)", "visual": "Box 1 (Purple #9b59b6): Raw markdown brain-dump and voice transcription.", "base_vo": "Tell: dump your raw thoughts directly into Obsidian.", "ai_punchy": "Tell: brain-dump raw thoughts into Obsidian.", "ai_strategic": "Stage 1 captures unstructured cognitive context in Obsidian.", "ai_conversational": "Step 1 is Tell: brain-dump your thoughts into Obsidian."},
    {"start": 129, "end": 134, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Step 2: Show (Canva)", "visual": "Box 2 (Orange #e67e22): Visual canvas maps relationships and sticky notes.", "base_vo": "Show: map visual relationships in Canva.", "ai_punchy": "Show: visualize concepts and structure in Canva.", "ai_strategic": "Stage 2 models visual representations and spatial flow in Canva.", "ai_conversational": "Step 2 is Show: map your visual structure in Canva."},
    {"start": 134, "end": 139, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Step 3: Do (Slide Decks)", "visual": "Box 3 (Red #c0392b): Presentation slide layouts render into consumable decks.", "base_vo": "Do: turn concepts into consumable slide decks.", "ai_punchy": "Do: turn ideas into consumable presentations.", "ai_strategic": "Stage 3 transforms architecture into pedagogical presentation decks.", "ai_conversational": "Step 3 is Do: turn those concepts into consumable slides."},
    {"start": 139, "end": 145, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Step 4: Apply (GitHub Code)", "visual": "Box 4 (Green #27ae60): Git commit push, code releases, and video assets ship.", "base_vo": "Apply: ship it as production code in GitHub.", "ai_punchy": "Apply: ship code and assets in GitHub.", "ai_strategic": "Stage 4 deploys functional code and automations to GitHub.", "ai_conversational": "Step 4 is Apply: ship real code and assets in GitHub."},
    {"start": 145, "end": 153, "scene": 5, "stage": "05", "name": "The 4-Step Workflow", "beat": "Chaos to Shipped Execution", "visual": "All 4 boxes light up with green checkmarks connecting start to finish.", "base_vo": "From chaos to execution in four clear steps.", "ai_punchy": "From chaos to execution in four steps.", "ai_strategic": "A repeatable closed-loop system from concept to deployment.", "ai_conversational": "From total chaos to finished execution in four steps."},

    # Scene 6: Call to Action & Cohort Launch (2:33 - 3:20)
    {"start": 153, "end": 159, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Building Your Second Brain", "visual": "Central AI Brain avatar pulses with golden energy and lightning arcs.", "base_vo": "This is about building an AI brain that actually works for you.", "ai_punchy": "Build an AI brain that works for you.", "ai_strategic": "Elevate your engineering capacity with autonomous agent systems.", "ai_conversational": "This is about building a second brain that truly works for you."},
    {"start": 159, "end": 166, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Accelerate AI Readiness", "visual": "Certification pathways, study cards, and agent badges orbit the brain.", "base_vo": "Accelerate your AI skills and prepare for top certifications.", "ai_punchy": "Accelerate your AI engineering readiness.", "ai_strategic": "Systematic preparation for enterprise AI architecture certifications.", "ai_conversational": "Accelerate your skills and prep for the biggest AI certifications."},
    {"start": 166, "end": 175, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Hands-on Sunday Cohort", "visual": "Sunday cohort schedule card highlights live weekly sessions (Every Sunday 9-11PM UK).", "base_vo": "Join our free hands-on Sunday cohort to build this live.", "ai_punchy": "Join our free weekly hands-on Sunday cohort.", "ai_strategic": "Participate in collaborative weekly live engineering workshops.", "ai_conversational": "Join our free live Sunday cohort and build this with us."},
    {"start": 175, "end": 185, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Build Architecture Together", "visual": "Step-by-step cohort roadmap and template repository links appear.", "base_vo": "We will build this entire architecture together from scratch.", "ai_punchy": "Build this entire architecture from scratch with us.", "ai_strategic": "Hands-on implementation of the full multi-agent PARA stack.", "ai_conversational": "We'll build this complete architecture together step by step."},
    {"start": 185, "end": 195, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Links In Comments", "visual": "Animated arrows point down to community Discord, GitHub, and registration links.", "base_vo": "Links are in the description and comments below.", "ai_punchy": "Links in the description and comments below.", "ai_strategic": "Access all repositories, templates, and registration links below.", "ai_conversational": "All the templates and links are in the description below."},
    {"start": 195, "end": 201, "scene": 6, "stage": "06", "name": "Call to Action & Closing", "beat": "Outro & Call To Action", "visual": "Branded outro card with subscribe, GitHub star, and cohort registration buttons.", "base_vo": "Let's build together. See you this Sunday.", "ai_punchy": "Let's build together. See you Sunday. Let's go.", "ai_strategic": "Begin your architecture implementation today. See you Sunday.", "ai_conversational": "Let's build together. See you in the cohort this Sunday!"}
]

def format_tc(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def get_beat_for_sec(sec: int) -> dict:
    for b in MASTER_BEATS:
        if b["start"] <= sec < b["end"]:
            return b
    return MASTER_BEATS[-1]

def get_video_duration(video_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ Could not read duration via ffprobe ({e}). Defaulting to 200s.")
        return 200.0

def find_target_video(input_dir: str, explicit_video: str = None) -> str:
    if explicit_video and os.path.exists(explicit_video):
        return explicit_video
    
    candidates = glob.glob(os.path.join(input_dir, "*.mp4")) + glob.glob(os.path.join(input_dir, "*.mov"))
    if candidates:
        return sorted(candidates)[0]
    
    fallback_clips = glob.glob("video_flow/*.mp4")
    if fallback_clips:
        print(f"ℹ️ No video found in {input_dir}. Using sample video from video_flow/ for demonstration.")
        return sorted(fallback_clips)[0]
    
    return ""

def extract_screenshots(video_path: str, output_dir: str, fps: float = 1.0) -> list:
    os.makedirs(output_dir, exist_ok=True)
    out_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    
    print(f"🎞️ Extracting 1 frame every {1/fps:.1f}s from: {video_path}")
    print(f"📂 Output destination: {output_dir}")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        out_pattern
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    extracted_files = sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))
    print(f"✅ Extracted {len(extracted_files)} frame screenshots.")
    return extracted_files

def build_manifest_and_docs(video_path: str, frames: list, fps: float = 1.0):
    duration = get_video_duration(video_path) if video_path else len(frames)
    video_name = os.path.basename(video_path) if video_path else "raw_video.mp4"
    
    manifest_entries = []
    
    for idx, fpath in enumerate(frames, start=1):
        sec = int(round((idx - 1) / fps))
        beat = get_beat_for_sec(sec)
        rel_fpath = os.path.relpath(fpath, start=os.path.dirname(DEFAULT_MD_DOC))
        
        manifest_entries.append({
            "index": idx,
            "second": sec,
            "timecode": format_tc(sec),
            "image_file": os.path.basename(fpath),
            "image_path": fpath,
            "rel_path": rel_fpath,
            "stage": beat["stage"],
            "scene_num": beat["scene"],
            "scene_name": beat["name"],
            "beat_title": beat["beat"],
            "visual_action": beat["visual"],
            "base_vo": beat["base_vo"],
            "ai_punchy": beat["ai_punchy"],
            "ai_strategic": beat["ai_strategic"],
            "ai_conversational": beat["ai_conversational"]
        })
    
    # Save JSON Manifest
    with open(DEFAULT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "video_source": video_name,
            "total_duration_sec": duration,
            "total_frames": len(manifest_entries),
            "frames": manifest_entries
        }, f, indent=2)
    print(f"💾 Saved JSON manifest: {DEFAULT_MANIFEST}")

    # Generate Markdown Document
    md_lines = [
        "# 🎙️ Voiceover In-Situ Rewrite Workbench",
        f"> **Source Video**: `{video_name}` | **Extracted Frames**: {len(manifest_entries)} | **Pacing Target**: 140–160 WPM (~3 words/sec)",
        f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Tactic**: 1-Second Frame Extraction & Visual AI Scripting",
        "",
        "---",
        "",
        "## 🛠️ How to Use This Workbench",
        "1. Inspect each **1-second screenshot** below to see exactly what visual motion graphic or Canva slide is on screen.",
        "2. Review the **Visual Action** and **AI-Suggested Variations** (Punchy, Strategic, Conversational).",
        "3. Write your **Final Resonant Voiceover** directly in the `[My Resonant Take]` block at ~3 words/second.",
        "4. Copy the final script back to `research.html` or record directly into your microphone.",
        "",
        "---",
        ""
    ]
    
    current_scene = None
    for entry in manifest_entries:
        if entry["scene_num"] != current_scene:
            current_scene = entry["scene_num"]
            md_lines.extend([
                f"## 🎬 Scene {entry['scene_num']}: {entry['scene_name']} `[{entry['timecode']}]`",
                f"**Baseline Script Reference**: *\"{entry['base_vo']}\"*",
                "",
            ])
        
        md_lines.extend([
            f"### ⏱️ Timestamp: `{entry['timecode']}` (Second {entry['second']}) · **{entry['beat_title']}**",
            f"**Visual Action**: *{entry['visual_action']}*",
            "",
            f"![Frame at {entry['timecode']}]({entry['rel_path']})",
            "",
            "| Option | Voiceover Candidate Text | WPM | Tone |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Scratch VO** | {entry['base_vo']} | ~150 | Baseline |",
            f"| **⚡ AI Punchy** | {entry['ai_punchy']} | ~165 | Energetic / Fast |",
            f"| **🧠 AI Strategic** | {entry['ai_strategic']} | ~140 | Pedagogical / Authoritative |",
            f"| **🔥 AI Conversational** | {entry['ai_conversational']} | ~145 | Direct & Relatable |",
            "",
            "> ✍️ **[My Resonant Take]**:",
            f"> *{entry['base_vo']}*",
            "",
            "---",
            ""
        ])
    
    with open(DEFAULT_MD_DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"📝 Generated Markdown Workbench: {DEFAULT_MD_DOC}")

    # Generate Interactive HTML Inspector
    generate_html_inspector(manifest_entries, video_name, duration)

def generate_html_inspector(manifest_entries: list, video_name: str, duration: float):
    manifest_json_str = json.dumps(manifest_entries)
    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voiceover Frame Inspector — WIG Animation</title>
<style>
:root {{
  --bg:#0c0c12; --panel:#161622; --ink:#f4f4f8; --muted:#9498a8;
  --line:#262638; --gold:#e8b84a; --cyan:#4ed8eb; --chip:#1e1e2d;
  --accent:#e74c3c; --accent2:#6366f1; --accent3:#27ae60; --purple:#af52de;
  --card-bg:#161622; --card-hover:#1c1c2b; --shadow:0 4px 20px rgba(0,0,0,0.35);
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.5; }}
header {{ position:sticky; top:0; z-index:50; background:var(--panel); border-bottom:1px solid var(--line); padding:10px 16px; box-shadow:0 2px 10px rgba(0,0,0,0.1); }}
.header-bar {{ max-width:1440px; margin:0 auto; display:flex; flex-wrap:wrap; align-items:center; gap:10px 14px; }}
.title {{ font-weight:800; font-size:16px; letter-spacing:.02em; display:flex; align-items:center; gap:8px; }}
.title a {{ color:inherit; text-decoration:none; }}
.shared-nav {{ display:inline-flex; flex-wrap:wrap; gap:4px; align-items:center; margin-right:auto; background:var(--chip); padding:4px; border-radius:10px; border:1px solid var(--line); }}
.shared-nav a {{ color:var(--muted); text-decoration:none; font-weight:600; font-size:13px; padding:6px 12px; border-radius:8px; transition:all 0.2s ease; display:inline-flex; align-items:center; gap:6px; }}
.shared-nav a:hover {{ color:var(--cyan); background:var(--panel); }}
.shared-nav a.active {{ color:var(--ink); background:var(--panel); box-shadow:0 1px 3px rgba(0,0,0,0.1); border:1px solid var(--line); }}
.btn {{ font:inherit; font-size:12.5px; font-weight:650; cursor:pointer; border:1px solid var(--line); background:var(--chip); color:var(--ink); border-radius:8px; padding:7px 12px; display:inline-flex; align-items:center; gap:6px; transition:all 0.15s ease; text-decoration:none; }}
.btn:hover {{ border-color:var(--cyan); color:var(--cyan); text-decoration:none; }}
.btn.primary {{ background:var(--accent2); border-color:var(--accent2); color:#fff; }}
.btn.success {{ background:var(--accent3); border-color:var(--accent3); color:#fff; }}
.btn.blue {{ background:#2563eb; border-color:#2563eb; color:#fff; }}
.btn.blue:hover {{ background:#1d4ed8; border-color:#1d4ed8; color:#fff; }}

/* Sticky Stats Bar */
.sticky-stats-bar {{
  position:sticky; top:57px; z-index:40; background:rgba(22,22,34,0.95); backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line); padding:10px 16px;
}}
.stats-bar-inner {{
  max-width:1440px; margin:0 auto; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px;
}}
.metric-pill {{
  display:inline-flex; align-items:center; gap:6px; background:var(--chip); border:1px solid var(--line);
  padding:5px 12px; border-radius:8px; font-size:12.5px; font-weight:600;
}}
.metric-val {{ font-weight:800; color:var(--cyan); }}
.azure-pill {{
  font-size:11.5px; font-weight:750; padding:5px 10px; border-radius:8px;
  background:rgba(78,216,235,0.12); color:var(--cyan); border:1px solid rgba(78,216,235,0.3);
  display:inline-flex; align-items:center; gap:5px;
}}

/* View Switcher */
.view-switch {{
  display:inline-flex; background:var(--chip); padding:3px; border-radius:8px; border:1px solid var(--line);
}}
.view-btn {{
  background:transparent; border:none; color:var(--muted); font:inherit; font-size:12px; font-weight:700;
  padding:5px 10px; border-radius:6px; cursor:pointer; display:inline-flex; align-items:center; gap:5px;
  transition:all .15s ease;
}}
.view-btn.active {{
  background:var(--panel); color:var(--ink); box-shadow:0 1px 3px rgba(0,0,0,0.2); border:1px solid var(--line);
}}

/* Main Container */
.container {{ max-width:1440px; margin:0 auto; padding:20px 16px 80px; }}

/* Slide Show Mode Panel */
.slideshow-panel {{
  background:var(--panel); border:1px solid var(--line); border-radius:14px; overflow:hidden;
  box-shadow:var(--shadow); margin-top:20px; display:none; flex-direction:column;
}}
.slideshow-stage {{
  position:relative; aspect-ratio:16/9; background:#000; width:100%; max-height:560px; overflow:hidden;
}}
.slideshow-stage img {{
  width:100%; height:100%; object-fit:contain; background:#000;
}}
.slideshow-controls {{
  background:var(--chip); border-top:1px solid var(--line); border-bottom:1px solid var(--line);
  padding:14px 20px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:14px;
}}
.nav-btn-group {{
  display:flex; align-items:center; gap:8px;
}}
.nav-btn {{
  background:var(--panel); border:1px solid var(--line); color:var(--ink); font:inherit; font-size:13px;
  font-weight:750; padding:8px 14px; border-radius:8px; cursor:pointer; display:inline-flex; align-items:center;
  gap:6px; transition:all .15s ease;
}}
.nav-btn:hover {{ border-color:var(--cyan); color:var(--cyan); }}
.nav-btn.primary {{ background:var(--accent2); border-color:var(--accent2); color:#fff; }}
.scrubber-wrap {{
  flex:1; min-width:240px; display:flex; align-items:center; gap:10px;
}}
.scrubber-slider {{
  flex:1; accent-color:var(--cyan); cursor:pointer;
}}
.slideshow-body {{
  padding:20px 24px; display:flex; flex-direction:column; gap:14px;
}}

/* Streamlined Inspector Grid (Image + Textbox) */
.inspector-grid {{
  display:grid; grid-template-columns:repeat(auto-fill, minmax(360px, 1fr)); gap:20px; margin-top:20px;
}}
.frame-card {{
  background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden;
  display:flex; flex-direction:column; box-shadow:var(--shadow); transition:transform .15s ease, border-color .15s ease;
}}
.frame-card:hover {{ border-color:var(--cyan); }}
.frame-thumb {{ position:relative; aspect-ratio:16/9; background:#000; overflow:hidden; }}
.frame-thumb img {{ width:100%; height:100%; object-fit:cover; display:block; }}
.tc-badge {{ position:absolute; bottom:8px; right:8px; background:rgba(0,0,0,0.85); color:#fff; font-family:monospace; font-size:12px; font-weight:700; padding:3px 7px; border-radius:4px; }}
.stage-badge {{ position:absolute; top:8px; left:8px; background:var(--accent2); color:#fff; font-size:10.5px; font-weight:700; padding:3px 8px; border-radius:4px; }}

/* Frame Body */
.frame-body {{ padding:14px; display:flex; flex-direction:column; gap:10px; flex:1; }}
.ai-pills-row {{ display:flex; flex-wrap:wrap; gap:6px; }}
.ai-quick-btn {{
  background:var(--chip); border:1px solid var(--line); border-radius:6px; padding:4px 8px;
  font-size:11px; font-weight:700; color:var(--muted); cursor:pointer; transition:all .15s ease;
  display:inline-flex; align-items:center; gap:4px;
}}
.ai-quick-btn:hover {{ border-color:var(--cyan); color:var(--cyan); }}
.ai-quick-btn.active {{ background:rgba(39,174,96,0.15); border-color:var(--accent3); color:var(--accent3); }}

/* Custom Resonant Textbox */
.textbox-label {{
  font-size:11.5px; font-weight:750; color:var(--gold); display:flex; justify-content:space-between; align-items:center;
}}
.custom-input {{
  width:100%; background:var(--bg); border:1px solid var(--line); border-radius:8px; color:var(--ink);
  font:inherit; font-size:13px; line-height:1.45; padding:10px 12px; resize:vertical; min-height:80px;
  transition:border-color .15s ease;
}}
.custom-input:focus {{ outline:none; border-color:var(--cyan); }}

/* Bottom Final Voiceover Section */
.final-vo-panel {{
  background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:24px 28px;
  margin-top:40px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:16px;
}}
.final-vo-header {{
  display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px;
}}
.final-vo-textarea {{
  width:100%; background:var(--bg); border:1px solid var(--line); border-radius:10px; color:var(--ink);
  font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:13px; line-height:1.55;
  padding:16px; min-height:260px; resize:vertical;
}}
.final-vo-textarea:focus {{ outline:none; border-color:var(--cyan); }}

.toast {{
  position:fixed; bottom:24px; right:24px; z-index:100; background:var(--ink); color:var(--bg);
  padding:10px 18px; border-radius:8px; font-size:13px; font-weight:750; opacity:0; pointer-events:none;
  transition:opacity .2s ease; box-shadow:0 4px 16px rgba(0,0,0,0.4);
}}
.toast.show {{ opacity:1; }}

/* Print / PDF Storyboard Styles (Image + Voice + Voiceover) */
@media print {{
  @page {{
    size: A4 portrait;
    margin: 10mm 12mm;
  }}
  body {{
    background: #fff !important;
    color: #111 !important;
    font-size: 10pt !important;
  }}
  header, .sticky-stats-bar, .shared-nav, .ai-pills-row, .btn, .view-switch, .azure-pill, #gridControlBar, .slideshow-panel, .final-vo-panel, .toast, footer {{
    display: none !important;
  }}
  .container {{
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }}
  .inspector-grid {{
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 14px !important;
    margin-top: 0 !important;
  }}
  .frame-card {{
    background: #fff !important;
    border: 1px solid #ccc !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    color: #111 !important;
    display: flex !important;
    flex-direction: column !important;
  }}
  .frame-thumb {{
    background: #000 !important;
    max-height: 160px !important;
  }}
  .frame-thumb img {{
    object-fit: cover !important;
  }}
  .stage-badge, .tc-badge {{
    background: rgba(0,0,0,0.85) !important;
    color: #fff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  .frame-body {{
    padding: 10px !important;
    gap: 6px !important;
  }}
  .custom-input {{
    background: #fdfdfd !important;
    color: #000 !important;
    border: 1px solid #bbb !important;
    font-size: 9.5pt !important;
    min-height: 55px !important;
    resize: none !important;
  }}
}}
</style>
</head>
<body>

<header>
  <div class="header-bar">
    <div class="title"><a href="../../index.html">WIG Animation</a></div>
    <nav class="shared-nav" aria-label="Main Navigation">
      <a href="../../index.html" class="nav-item"><span>🏠</span> Overview</a>
      <a href="../../research.html" class="nav-item"><span>🎬</span> Research</a>
      <a href="../../gallery.html" class="nav-item"><span>🖼️</span> Gallery</a>
      <a href="../../scenes.html" class="nav-item"><span>🗂️</span> Scenes</a>
      <a href="../../timeline.html" class="nav-item"><span>↔️</span> Timeline</a>
      <a href="../../shotlist.html" class="nav-item"><span>📊</span> Shot List</a>
      <a href="../../voice_over.html" class="nav-item"><span>📜</span> VoiceOver</a>
      <a href="../../tactic.html" class="nav-item"><span>🎯</span> Tactics</a>
      <a href="../../analysis.html" class="nav-item"><span>📈</span> Analysis</a>
      <a href="../../script_guru.html" class="nav-item"><span>🧙‍♂️</span> Script Guru</a>
      <a href="voiceover_inspector.html" class="nav-item active"><span>🎙️</span> VO Inspector</a>
      <a href="https://canva.link/p4u3nwvsmio19jp" class="nav-item" target="_blank" rel="noopener noreferrer" style="color:var(--purple,#af52de);" title="Canva Implementation Deck"><span>🎨</span> Implementation ↗</a>
    </nav>
    <button class="btn purple" onclick="openAIVoiceoverModal()" style="background:linear-gradient(135deg, #8e44ad, #6366f1); border-color:#8e44ad; color:#fff; font-weight:800; box-shadow:0 2px 10px rgba(142,68,173,0.35);">✨ AI Voiceover (Gemini)</button>
    <button class="btn primary" onclick="scrollToFinalVO()">📋 Generate Final Voiceover</button>
    <button class="btn success" onclick="downloadHTMLDoc()" title="Save all changes and download updated voiceover_inspector.html">💾 Save &amp; Download HTML</button>
    <button class="btn blue" onclick="downloadPlainTextVO()" title="Download spoken voiceover audio text only (.txt)">🎙️ Download Voiceover</button>
    <button class="btn" onclick="downloadAzureVoiceoverTxt()" title="Download synced Azure Blob object containing voiceover as a text file">☁️ Download Azure VO (.txt)</button>
    <button class="btn" onclick="downloadAsPDF()" title="Download storyboard cards as PDF (Image + Voice + Voiceover)">📄 Download as PDF</button>
    <a href="https://www.canva.com/design/DAHRZe5KBoA/OJU0sL318CozUaTBpkdT2g/edit" class="btn" target="_blank" rel="noopener noreferrer" style="color:var(--purple,#af52de);border-color:rgba(175,82,222,0.35);background:rgba(175,82,222,0.1);" title="Open Canva Document">🎨 Canva Document ↗</a>
  </div>
</header>

<!-- Sticky Stats & Word Count Bar -->
<div class="sticky-stats-bar">
  <div class="stats-bar-inner">
    <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px;">
      <div class="view-switch">
        <button type="button" class="view-btn active" id="btnGridView" onclick="setViewMode('grid')">📱 Grid View</button>
        <button type="button" class="view-btn" id="btnSlideView" onclick="setViewMode('slideshow')">📽️ Slide Show Mode</button>
      </div>
      <div class="metric-pill"><span>📝 Word Count:</span> <span class="metric-val" id="metricWordCount">0 words</span></div>
      <div class="metric-pill"><span>⏱️ Estimated Audio:</span> <span class="metric-val" id="metricAudioDuration">0:00</span> <small style="color:var(--muted);">(150 WPM)</small></div>
      <div class="metric-pill"><span>🎞️ Video Length:</span> <span class="metric-val" id="metricVideoLength">{format_tc(int(duration))} ({int(duration)}s)</span></div>
      <div class="metric-pill" id="metricPacingStatus"><span>🎯 Pacing:</span> <span style="color:#27ae60;font-weight:750;">Calculating...</span></div>
    </div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div class="azure-pill" id="azureStat">☁️ Azure Synced</div>
      <button class="btn purple" onclick="openAIVoiceoverModal()" style="background:linear-gradient(135deg, #8e44ad, #6366f1); border-color:#8e44ad; color:#fff; font-weight:800;">✨ AI Voiceover (Gemini)</button>
      <button class="btn" onclick="saveToAzure(true)">☁️ Save to Azure</button>
      <button class="btn success" onclick="downloadHTMLDoc()" title="Download current HTML page with all edits baked in">📥 Download HTML</button>
      <button class="btn blue" onclick="downloadPlainTextVO()" title="Download spoken plain text voiceover only (.txt)">🎙️ Download Voiceover</button>
      <button class="btn" onclick="downloadAzureVoiceoverTxt()" title="Download synced Azure Blob object containing voiceover as a text file">☁️ Download Azure VO</button>
      <button class="btn" onclick="downloadAsPDF()" title="Download storyboard as PDF (Image + Voice + Voiceover)">📄 Download PDF</button>
    </div>
  </div>
</div>

<!-- AI Voiceover Studio Modal Popup -->
<div id="aiVoiceoverModal" class="ai-modal-overlay" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); backdrop-filter:blur(6px); z-index:9999; align-items:center; justify-content:center; padding:16px;">
  <div class="ai-modal-content" style="background:var(--panel); border:1px solid var(--line); border-radius:16px; max-width:860px; width:100%; max-height:90vh; overflow-y:auto; padding:28px; box-shadow:0 20px 50px rgba(0,0,0,0.5); display:flex; flex-direction:column; gap:18px;">
    
    <!-- Modal Header -->
    <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid var(--line); padding-bottom:14px;">
      <div>
        <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(142,68,173,0.15); color:var(--purple); padding:4px 10px; border-radius:999px; font-size:11.5px; font-weight:750; margin-bottom:6px;">
          <span>⚡</span> Powered by Google Gemini &amp; Azure Key Vault
        </div>
        <h2 style="margin:0; font-size:22px; font-weight:850; display:flex; align-items:center; gap:8px;">
          <span>✨</span> Gemini AI Voiceover Studio
        </h2>
        <p style="margin:4px 0 0; color:var(--muted); font-size:13px;">
          Generates a synchronized 200-second voiceover script using keys from Azure Key Vault (<code>dp-kv-deliverypilot</code>).
        </p>
      </div>
      <button type="button" class="btn" onclick="closeAIVoiceoverModal()" style="font-size:16px; padding:4px 10px;">✖</button>
    </div>

    <!-- 3 Target Parameter Cards -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">
      <div style="background:var(--chip); border:1px solid var(--line); border-left:4px solid var(--purple); border-radius:10px; padding:12px 14px;">
        <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:750;">Persona &amp; Tone</div>
        <div style="font-size:13.5px; font-weight:800; color:var(--ink); margin-top:2px;">Erdem's Booming Resonance</div>
        <div style="font-size:11.5px; color:var(--muted); margin-top:2px;">Ali Abdaal 3-Act Retention</div>
      </div>
      <div style="background:var(--chip); border:1px solid var(--line); border-left:4px solid var(--cyan); border-radius:10px; padding:12px 14px;">
        <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:750;">Pacing Target</div>
        <div style="font-size:13.5px; font-weight:800; color:var(--ink); margin-top:2px;">3 Words / Second</div>
        <div style="font-size:11.5px; color:var(--muted); margin-top:2px;">~150 Spoken Words Per Minute</div>
      </div>
      <div style="background:var(--chip); border:1px solid var(--line); border-left:4px solid var(--accent3); border-radius:10px; padding:12px 14px;">
        <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:750;">Timeline Scope</div>
        <div style="font-size:13.5px; font-weight:800; color:var(--ink); margin-top:2px;">200s (03:20 Total)</div>
        <div style="font-size:11.5px; color:var(--muted); margin-top:2px;">Full Coverage (Scenes 1 &rarr; 6)</div>
      </div>
    </div>

    <!-- Prompt & Context Inspector -->
    <div>
      <label style="font-size:12.5px; font-weight:750; color:var(--ink); display:block; margin-bottom:6px;">
        📝 Custom Prompt &amp; Narrative Directives:
      </label>
      <textarea id="aiPromptInput" style="width:100%; background:var(--bg); border:1px solid var(--line); border-radius:8px; color:var(--ink); font-size:12.5px; padding:10px 12px; height:90px; resize:vertical; line-height:1.45;">Generate the master 200-second voiceover script for Rifat Erdem Sahin covering:
- Scene 1 [00:00 - 00:18]: Drowning in 46,000 Obsidian notes.
- Scene 2 [00:19 - 00:48]: The breakthrough: AI Knowledge Engine running background synthesis.
- Scene 3 [00:49 - 01:24]: P.A.R.A. Framework (Projects, Areas, Resources, Archive).
- Scene 4 [01:25 - 01:58]: Dual-Agent Orchestration (Gemini + Claude syncing GitHub/Drive/Proxmox).
- Scene 5 [01:59 - 02:32]: The 4-Step Conveyor Loop: Tell -> Show -> Do -> Apply.
- Scene 6 [02:33 - 03:20]: Resolution: Second brain awakening + Free Sunday live cohort build CTA.</textarea>
    </div>

    <!-- Generated Output Preview Area -->
    <div>
    <!-- 1st Sentence API Endpoint Tester Row -->
    <div style="background:var(--chip); border:1px solid var(--line); border-radius:10px; padding:12px 14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
        <div style="font-size:12px; font-weight:800; color:var(--ink); display:flex; align-items:center; gap:6px;">
          <span>🧪</span> Endpoint Quick-Testers (1st Sentence: <i>"I was drowning in 46,000 notes across Obsidian."</i>)
        </div>
        <span style="font-size:11px; color:var(--muted);">Test credentials &amp; latency instantly</span>
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:8px;">
        <button type="button" class="btn" onclick="testEndpoint('gemini')" style="border-color:var(--purple); color:var(--purple);">
          🧪 Test Gemini AI Script
        </button>
        <button type="button" class="btn" onclick="testEndpoint('elevenlabs')" style="border-color:#2563eb; color:#2563eb;">
          🔊 Test ElevenLabs Voice
        </button>
        <button type="button" class="btn" onclick="testEndpoint('fal')" style="border-color:var(--gold); color:var(--gold);">
          ⚡ Test Fal.ai Voice
        </button>
      </div>
      <audio id="aiAudioPlayer" controls style="width:100%; display:none; margin-top:10px; border-radius:8px;"></audio>
    </div>

    <!-- Generated Output Preview Area -->
    <div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <label style="font-size:12.5px; font-weight:750; color:var(--ink);">
          ⚡ AI Generated Script Preview:
        </label>
        <span id="aiGenStatus" style="font-size:11.5px; color:var(--muted);">Ready to generate</span>
      </div>
      <textarea id="aiPreviewOutput" placeholder="Click 'Generate Voiceover with Gemini AI' or 'Generate with Fal.ai' below to run the AI engine..." style="width:100%; background:var(--bg); border:1px solid var(--line); border-radius:8px; color:var(--cyan); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:12px; padding:12px; height:180px; resize:vertical; line-height:1.45;"></textarea>
    </div>

    <!-- Action Footer -->
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; border-top:1px solid var(--line); padding-top:14px;">
      <div style="font-size:11.5px; color:var(--muted);">
        🔑 Vault: <code>dp-kv-deliverypilot</code> (<code>GEMINI</code> · <code>ELEVENLABS</code> · <code>FAL-AI</code>)
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:8px;">
        <button type="button" class="btn" onclick="closeAIVoiceoverModal()">Cancel</button>
        <button type="button" class="btn purple" id="btnRunAIGen" onclick="runAIGeneration()" style="background:linear-gradient(135deg, #8e44ad, #6366f1); border-color:#8e44ad; color:#fff; font-weight:800;">
          🚀 Generate Voiceover (Gemini)
        </button>
        <button type="button" class="btn" id="btnRunFalGen" onclick="runFalAudioGeneration()" style="background:#f59e0b; border-color:#d97706; color:#000; font-weight:800;">
          ⚡ Generate Audio (Fal.ai)
        </button>
        <button type="button" class="btn success" id="btnApplyAIGen" onclick="applyAIGeneratedScript()" style="display:none;">
          💾 Apply to Voiceover Inspector &amp; Save
        </button>
      </div>
    </div>

  </div>
</div>
    <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px;">
      <div class="view-switch">
        <button type="button" class="view-btn active" id="btnGridView" onclick="setViewMode('grid')">📱 Grid View</button>
        <button type="button" class="view-btn" id="btnSlideView" onclick="setViewMode('slideshow')">📽️ Slide Show Mode</button>
      </div>
      <div class="metric-pill"><span>📝 Word Count:</span> <span class="metric-val" id="metricWordCount">0 words</span></div>
      <div class="metric-pill"><span>⏱️ Estimated Audio:</span> <span class="metric-val" id="metricAudioDuration">0:00</span> <small style="color:var(--muted);">(150 WPM)</small></div>
      <div class="metric-pill"><span>🎞️ Video Length:</span> <span class="metric-val" id="metricVideoLength">{format_tc(int(duration))} ({int(duration)}s)</span></div>
      <div class="metric-pill" id="metricPacingStatus"><span>🎯 Pacing:</span> <span style="color:#27ae60;font-weight:750;">Calculating...</span></div>
    </div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div class="azure-pill" id="azureStat">☁️ Azure Synced</div>
      <button class="btn" onclick="saveToAzure(true)">☁️ Save to Azure</button>
      <button class="btn success" onclick="downloadHTMLDoc()" title="Download current HTML page with all edits baked in">📥 Download HTML</button>
      <button class="btn blue" onclick="downloadPlainTextVO()" title="Download spoken plain text voiceover only (.txt)">🎙️ Download Voiceover</button>
      <button class="btn" onclick="downloadAzureVoiceoverTxt()" title="Download synced Azure Blob object containing voiceover as a text file">☁️ Download Azure VO</button>
      <button class="btn" onclick="downloadAsPDF()" title="Download storyboard as PDF (Image + Voice + Voiceover)">📄 Download PDF</button>
    </div>
  </div>
</div>

<div class="container">
  <!-- Slide Show Mode Panel -->
  <div class="slideshow-panel" id="slideshowPanel">
    <div class="slideshow-stage">
      <img id="slideImg" src="screenshots/{manifest_entries[0]['image_file']}" alt="Slide Frame">
      <span class="stage-badge" id="slideStageBadge">Scene 1 · Hook &amp; Problem Setup</span>
      <span class="tc-badge" id="slideTcBadge">00:00</span>
    </div>
    <div class="slideshow-controls">
      <div class="nav-btn-group">
        <button type="button" class="nav-btn" onclick="prevSlide()" title="Keyboard Left Arrow">⬅️ Prev Frame</button>
        <button type="button" class="nav-btn primary" onclick="toggleAutoPlay()" id="btnAutoPlay">▶️ Auto-Play</button>
        <button type="button" class="nav-btn" onclick="nextSlide()" title="Keyboard Right Arrow">Next Frame ➡️</button>
      </div>
      <div class="scrubber-wrap">
        <span style="font-size:12px; font-weight:700; color:var(--muted);" id="slideCounter">Frame 1 / {len(manifest_entries)}</span>
        <input type="range" class="scrubber-slider" min="0" max="{len(manifest_entries)-1}" value="0" id="slideScrubber" oninput="onScrub(this.value)">
      </div>
      <div>
        <button type="button" class="btn" onclick="setViewMode('grid')">✖️ Exit Slide Show</button>
      </div>
    </div>
    <div class="slideshow-body">
      <div id="slideVisualActionBox" style="font-size:12.5px; color:var(--muted); background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:8px; border-left:3px solid var(--cyan); line-height:1.4;">
        🎬 <b>Visual Action:</b> <span id="slideVisualAction" style="color:var(--ink);"></span>
      </div>
      <div class="ai-pills-row">
        <button type="button" class="ai-quick-btn" id="btnSlideConv" onclick="applySlideSuggestion('conv')">
          🔥 AI Conversational
        </button>
        <button type="button" class="ai-quick-btn" id="btnSlidePunchy" onclick="applySlideSuggestion('punchy')">
          ⚡ AI Punchy
        </button>
        <button type="button" class="ai-quick-btn" id="btnSlideStrat" onclick="applySlideSuggestion('strategic')">
          🧠 AI Strategic
        </button>
      </div>
      <div>
        <div class="textbox-label">
          <span id="slideTakeLabel">✍️ Custom Resonant Take (Second 0):</span>
          <span style="font-size:11.5px; color:var(--muted);" id="slideWordCount">0 w</span>
        </div>
        <textarea class="custom-input" id="slideTakeInput" oninput="onSlideTakeInput()" placeholder="Type your custom resonant voiceover for this frame…"></textarea>
      </div>
    </div>
  </div>

  <!-- Grid Mode Controls -->
  <div id="gridControlBar" style="background:var(--chip); border:1px solid var(--line); border-radius:10px; padding:16px 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <strong style="font-size:15px; font-weight:800;">1-Second Screen Visual Rewrite Inspector</strong>
      <div style="font-size:12.5px; color:var(--muted);">Total Seconds Extracted: {len(manifest_entries)} | Click <b>📽️ Slide Show Mode</b> for full-screen stepping with back/forth buttons.</div>
    </div>
    <div>
      <input type="search" id="filterInput" oninput="filterFrames()" placeholder="Filter by scene, second, or script keyword…" style="padding:7px 12px; font:inherit; font-size:12.5px; border-radius:6px; border:1px solid var(--line); background:var(--bg); color:var(--ink); min-width:260px;">
    </div>
  </div>

  <!-- Streamlined Grid: 1 Image -> Textbox -->
  <div class="inspector-grid" id="grid">
"""

    for e in manifest_entries:
        escaped_punchy = e['ai_punchy'].replace('`', '').replace('"', '&quot;')
        escaped_strategic = e['ai_strategic'].replace('`', '').replace('"', '&quot;')
        escaped_conv = e['ai_conversational'].replace('`', '').replace('"', '&quot;')
        escaped_visual = e['visual_action'].replace('"', '&quot;')
        
        html_content += f"""
    <div class="frame-card" data-sec="{e['second']}" data-scene="{e['scene_num']}" data-beat="{e['beat_title']}">
      <div class="frame-thumb" onclick="openSlideAt({e['second']})" style="cursor:pointer;" title="Click to view in Slide Show Mode">
        <img src="screenshots/{e['image_file']}" alt="Second {e['second']}" loading="lazy">
        <span class="stage-badge">Scene {e['scene_num']} · {e['scene_name']}</span>
        <span class="tc-badge">{e['timecode']}</span>
      </div>
      <div class="frame-body">
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:11.5px; font-weight:700; color:var(--cyan);">
          <span>🎯 {e['beat_title']}</span>
          <span style="color:var(--muted); font-size:10.5px; font-weight:600;">Second {e['second']}/200</span>
        </div>
        <div style="font-size:11.5px; color:var(--muted); background:rgba(255,255,255,0.03); padding:5px 8px; border-radius:6px; border-left:3px solid var(--cyan); line-height:1.35;">
          🎬 <b>Visual:</b> {escaped_visual}
        </div>
        <div class="ai-pills-row">
          <button type="button" class="ai-quick-btn" tabindex="-1" onclick="applySuggestion({e['second']}, `{escaped_conv}`, this)" title="Click to fill conversational take">
            🔥 AI Conversational
          </button>
          <button type="button" class="ai-quick-btn" tabindex="-1" onclick="applySuggestion({e['second']}, `{escaped_punchy}`, this)" title="Click to fill punchy take">
            ⚡ AI Punchy
          </button>
          <button type="button" class="ai-quick-btn" tabindex="-1" onclick="applySuggestion({e['second']}, `{escaped_strategic}`, this)" title="Click to fill strategic take">
            🧠 AI Strategic
          </button>
        </div>
        <div>
          <div class="textbox-label">
            <span>✍️ Custom Resonant Take (Second {e['second']}):</span>
            <span style="font-size:11px; color:var(--muted);" id="wc_take_{e['second']}">0 w</span>
          </div>
          <textarea class="custom-input" id="take_{e['second']}" oninput="onTakeInput({e['second']})" placeholder="Type your custom resonant voiceover for this frame…">{e['base_vo']}</textarea>
        </div>
      </div>
    </div>
"""

    html_content += f"""
  </div>

  <!-- Bottom Final Voiceover Assembly & Generator Panel -->
  <div class="final-vo-panel" id="finalVoPanel">
    <div class="final-vo-header">
      <div>
        <span class="azure-pill" style="margin-bottom:6px;">🎙️ Complete Voiceover Output</span>
        <h2 style="margin:4px 0 0; font-size:18px; font-weight:800;">Generated Final Voiceover Script</h2>
        <div style="font-size:13px; color:var(--muted); margin-top:2px;">
          Assembled in real-time from all frame takes above. Ready to record, paste into ElevenLabs, or sync to Azure.
        </div>
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
        <button class="btn primary" onclick="copyFinalScript()">📋 Copy Full Script</button>
        <button class="btn" onclick="copyPlainTextVO()" title="Copy only the spoken voiceover text for ElevenLabs / TTS">🎙️ Copy Plain Text</button>
        <button class="btn success" onclick="saveToAzure(true)">☁️ Save to Azure</button>
        <button class="btn blue" onclick="downloadPlainTextVO()" title="Download plain text voiceover only (.txt)">🎙️ Download Voiceover (.txt)</button>
        <button class="btn" onclick="downloadAzureVoiceoverTxt()" title="Download synced Azure Blob object containing voiceover as a text file">☁️ Download Azure VO (.txt)</button>
        <button class="btn" onclick="downloadAsPDF()" title="Download storyboard as PDF (Image + Voice + Voiceover)">📄 Download as PDF</button>
        <button class="btn success" onclick="downloadHTMLDoc()" title="Download complete HTML inspector page">📥 Download HTML</button>
        <button class="btn" onclick="downloadScript()" title="Download script as markdown with timecodes">📥 Download .md</button>
        <button class="btn" onclick="downloadJSONState()" title="Download state as JSON">📥 Download JSON</button>
        <button class="btn" onclick="buildFinalVoiceover(true)">🔄 Re-Assemble</button>
      </div>
    </div>

    <textarea class="final-vo-textarea" id="finalVoiceoverOutput" readonly></textarea>
  </div>
</div>

<!-- Footer with Live Fly.io and GitHub Pages Links -->
<footer style="margin-top:40px; background:var(--panel); border-top:1px solid var(--line); padding:24px 16px; font-size:13px; color:var(--muted);">
  <div style="max-width:1440px; margin:0 auto; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:16px;">
    <div style="display:flex; flex-wrap:wrap; align-items:center; gap:12px;">
      <div style="background:rgba(37,99,235,0.12); border:1px solid rgba(37,99,235,0.3); padding:6px 12px; border-radius:8px; display:inline-flex; align-items:center; gap:6px;">
        <span>🚀 <strong>Live Fly.io App:</strong></span>
        <a href="https://aug-video-animation-1.fly.dev/3_Simulation/rawexport/voiceover_inspector.html" target="_blank" rel="noopener noreferrer" style="color:var(--cyan);font-weight:700;text-decoration:none;">
          https://aug-video-animation-1.fly.dev/3_Simulation/rawexport/voiceover_inspector.html ↗
        </a>
      </div>
      <div style="background:rgba(39,174,96,0.12); border:1px solid rgba(39,174,96,0.3); padding:6px 12px; border-radius:8px; display:inline-flex; align-items:center; gap:6px;">
        <span>🌐 <strong>Live GitHub Pages:</strong></span>
        <a href="https://rifaterdemsahin.github.io/aug-video-animation-1/3_Simulation/rawexport/voiceover_inspector.html" target="_blank" rel="noopener noreferrer" style="color:var(--accent3);font-weight:700;text-decoration:none;">
          https://rifaterdemsahin.github.io/aug-video-animation-1 ↗
        </a>
      </div>
    </div>
    <div style="display:flex; align-items:center; gap:10px;">
      <span>Repository: <a href="https://github.com/rifaterdemsahin/aug-video-animation-1" target="_blank" rel="noopener noreferrer" style="color:var(--ink);font-weight:600;">rifaterdemsahin/aug-video-animation-1</a></span>
    </div>
  </div>
</footer>

<div id="toast" class="toast"></div>

<script>
const MANIFEST_DATA = {manifest_json_str};
const STORAGE_PREFIX = "aug_vo_take_";
let currentSlideIndex = 0;
let autoPlayTimer = null;
// Initialize on page load
window.addEventListener("DOMContentLoaded", async () => {{
  setupKeyboardNav();
  await loadTakes();
}});

async function loadTakes(){{
  // 1. Load from localStorage first for instant paint
  loadSavedTakes();
  updateLiveMetrics();
  buildFinalVoiceover();

  // 2. Fetch latest synced state from Azure Blob Storage (/api/state)
  try {{
    const res = await fetch("/api/state", {{ cache: "no-store" }});
    if(res.ok){{
      const data = await res.json();
      if(data && data.ok && data.state && data.state.voiceoverCustomTakes){{
        const takes = data.state.voiceoverCustomTakes;
        let loadedCount = 0;
        Object.keys(takes).forEach(sec => {{
          const ta = document.getElementById('take_' + sec);
          if(ta && takes[sec]){{
            ta.value = takes[sec];
            try {{ localStorage.setItem(STORAGE_PREFIX + sec, takes[sec]); }}catch(e){{}}
            loadedCount++;
          }}
        }});
        const stat = document.getElementById('azureStat');
        if(stat) stat.textContent = "☁️ Azure Synced";
        updateLiveMetrics();
        buildFinalVoiceover();
        if(loadedCount > 0){{
          showToast('Loaded ' + loadedCount + ' takes from Azure Blob');
        }}
      }}
    }}
  }} catch(e){{
    // Running on static GitHub Pages or offline
    const stat = document.getElementById('azureStat');
    if(stat) stat.textContent = "💾 Local Storage";
  }}
}}

function setViewMode(mode){{
  const gridEl = document.getElementById('grid');
  const gridBar = document.getElementById('gridControlBar');
  const slidePanel = document.getElementById('slideshowPanel');
  const btnGrid = document.getElementById('btnGridView');
  const btnSlide = document.getElementById('btnSlideView');
  
  if(mode === 'slideshow'){{
    gridEl.style.display = 'none';
    gridBar.style.display = 'none';
    slidePanel.style.display = 'flex';
    btnGrid.classList.remove('active');
    btnSlide.classList.add('active');
    renderCurrentSlide();
    slidePanel.scrollIntoView({{ behavior: 'smooth' }});
  }} else {{
    stopAutoPlay();
    gridEl.style.display = 'grid';
    gridBar.style.display = 'flex';
    slidePanel.style.display = 'none';
    btnGrid.classList.add('active');
    btnSlide.classList.remove('active');
  }}
}}

function openSlideAt(second){{
  const idx = MANIFEST_DATA.findIndex(e => e.second === second);
  if(idx !== -1){{
    currentSlideIndex = idx;
  }}
  setViewMode('slideshow');
}}

function renderCurrentSlide(){{
  const item = MANIFEST_DATA[currentSlideIndex];
  if(!item) return;
  
  document.getElementById('slideImg').src = 'screenshots/' + item.image_file;
  document.getElementById('slideStageBadge').textContent = 'Scene ' + item.scene_num + ' · ' + item.scene_name + (item.beat_title ? (' | 🎯 ' + item.beat_title) : '');
  document.getElementById('slideTcBadge').textContent = item.timecode;
  document.getElementById('slideCounter').textContent = 'Frame ' + (currentSlideIndex + 1) + ' / ' + MANIFEST_DATA.length + ' (' + item.timecode + ')';
  document.getElementById('slideScrubber').value = currentSlideIndex;
  
  const visEl = document.getElementById('slideVisualAction');
  if(visEl) visEl.textContent = item.visual_action || 'Visual frame screen capture.';
  
  document.getElementById('slideTakeLabel').textContent = '✍️ Custom Resonant Take (Second ' + item.second + ' · ' + (item.beat_title || '') + '):';
  
  // Read value from grid textarea or localStorage
  const gridTa = document.getElementById('take_' + item.second);
  const val = gridTa ? gridTa.value : (localStorage.getItem(STORAGE_PREFIX + item.second) || item.base_vo);
  const slideTa = document.getElementById('slideTakeInput');
  slideTa.value = val;
  updateSlideWordCount(val);
}}

function onSlideTakeInput(){{
  const item = MANIFEST_DATA[currentSlideIndex];
  if(!item) return;
  const val = document.getElementById('slideTakeInput').value;
  
  // Sync to grid input
  const gridTa = document.getElementById('take_' + item.second);
  if(gridTa) gridTa.value = val;
  
  // Save to localStorage
  try{{ localStorage.setItem(STORAGE_PREFIX + item.second, val); }}catch(e){{}}
  
  updateSlideWordCount(val);
  updateCardWordCount(item.second, val);
  
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {{
    updateLiveMetrics();
    buildFinalVoiceover();
    saveToAzure(false);
  }}, 400);
}}

function applySlideSuggestion(type){{
  const item = MANIFEST_DATA[currentSlideIndex];
  if(!item) return;
  let text = item.ai_conversational;
  if(type === 'punchy') text = item.ai_punchy;
  if(type === 'strategic') text = item.ai_strategic;
  
  document.getElementById('slideTakeInput').value = text;
  onSlideTakeInput();
  showToast('Applied ' + type + ' take for Second ' + item.second + '!');
}}

function updateSlideWordCount(text){{
  const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
  document.getElementById('slideWordCount').textContent = words + ' w';
}}

function prevSlide(){{
  if(currentSlideIndex > 0){{
    currentSlideIndex--;
    renderCurrentSlide();
  }} else {{
    showToast("Beginning of video frames.");
  }}
}}

function nextSlide(){{
  if(currentSlideIndex < MANIFEST_DATA.length - 1){{
    currentSlideIndex++;
    renderCurrentSlide();
  }} else {{
    stopAutoPlay();
    showToast("Reached end of video frames.");
  }}
}}

function onScrub(val){{
  currentSlideIndex = parseInt(val, 10);
  renderCurrentSlide();
}}

function toggleAutoPlay(){{
  if(autoPlayTimer){{
    stopAutoPlay();
  }} else {{
    startAutoPlay();
  }}
}}

function startAutoPlay(){{
  const btn = document.getElementById('btnAutoPlay');
  btn.textContent = "⏸️ Pause";
  btn.style.background = "var(--accent)";
  autoPlayTimer = setInterval(() => {{
    if(currentSlideIndex < MANIFEST_DATA.length - 1){{
      nextSlide();
    }} else {{
      stopAutoPlay();
    }}
  }}, 1000);
}}

function stopAutoPlay(){{
  if(autoPlayTimer){{
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
    const btn = document.getElementById('btnAutoPlay');
    if(btn){{
      btn.textContent = "▶️ Auto-Play";
      btn.style.background = "var(--accent2)";
    }}
  }}
}}

// Keyboard Navigation Handler
function setupKeyboardNav(){{
  window.addEventListener('keydown', (e) => {{
    const activeEl = document.activeElement;
    const isTyping = activeEl && (activeEl.tagName === 'TEXTAREA' || activeEl.tagName === 'INPUT');
    
    // Tab and Shift+Tab navigation exclusively across textboxes in Grid View
    if(e.key === 'Tab'){{
      if(activeEl && activeEl.classList.contains('custom-input') && activeEl.id.startsWith('take_')){{
        e.preventDefault();
        const allInputs = Array.from(document.querySelectorAll('.inspector-grid .custom-input'));
        const currentIndex = allInputs.indexOf(activeEl);
        
        let targetIndex = e.shiftKey ? currentIndex - 1 : currentIndex + 1;
        if(targetIndex >= 0 && targetIndex < allInputs.length){{
          const targetInput = allInputs[targetIndex];
          targetInput.focus();
          targetInput.select();
          const card = targetInput.closest('.frame-card');
          if(card){{
            card.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
          }}
          const sec = targetInput.id.replace('take_', '');
          showToast('Focused Second ' + sec + ' textbox');
        }}
        return;
      }}
    }}
    
    // In Slideshow mode, Left/Right arrow keys navigate if not typing
    if(document.getElementById('slideshowPanel').style.display === 'flex'){{
      if(e.key === 'ArrowLeft' && !isTyping){{
        e.preventDefault();
        prevSlide();
      }} else if((e.key === 'ArrowRight' || e.key === ' ') && !isTyping){{
        e.preventDefault();
        nextSlide();
      }} else if(e.key === 'Escape'){{
        setViewMode('grid');
      }}
    }}
  }});
}}

// Load takes from localStorage/cookie
function loadSavedTakes(){{
  document.querySelectorAll('.custom-input').forEach(ta => {{
    const sec = ta.id.replace('take_', '');
    const saved = localStorage.getItem(STORAGE_PREFIX + sec);
    if(saved !== null){{
      ta.value = saved;
    }}
  }});
}}

// On take input change in Grid Mode
function onTakeInput(sec){{
  const ta = document.getElementById('take_' + sec);
  if(!ta) return;
  const val = ta.value;
  
  // Save to localStorage
  try{{ localStorage.setItem(STORAGE_PREFIX + sec, val); }}catch(e){{}}
  
  updateCardWordCount(sec, val);
  
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {{
    updateLiveMetrics();
    buildFinalVoiceover();
    saveToAzure(false);
  }}, 400);
}}

function applySuggestion(sec, text, btn){{
  const ta = document.getElementById('take_' + sec);
  if(!ta) return;
  ta.value = text;
  onTakeInput(sec);
  
  const parent = btn.closest('.ai-pills-row');
  parent.querySelectorAll('.ai-quick-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  showToast('Applied suggestion for Second ' + sec + '!');
}}

function updateCardWordCount(sec, text){{
  const el = document.getElementById('wc_take_' + sec);
  if(el){{
    const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
    el.textContent = words + ' w';
  }}
}}

// Calculate live script metrics
function updateLiveMetrics(){{
  const uniqueTakes = getCleanSequentialTakes();
  const fullText = uniqueTakes.map(t => t.text).join(' ');
  const wordCount = fullText.trim() ? fullText.trim().split(/\\s+/).length : 0;
  
  const estSeconds = Math.round((wordCount / 150) * 60);
  const estMin = Math.floor(estSeconds / 60);
  const estSec = estSeconds % 60;
  const estFormatted = estMin + ':' + estSec.toString().padStart(2, '0');
  
  document.getElementById('metricWordCount').textContent = wordCount + ' words';
  document.getElementById('metricAudioDuration').textContent = estFormatted;
  
  const videoSec = 200;
  const pacingEl = document.getElementById('metricPacingStatus');
  const delta = videoSec - estSeconds;
  if(delta >= 0 && delta <= 30){{
    pacingEl.innerHTML = '<span>🎯 Pacing:</span> <span style="color:#27ae60;font-weight:750;">Perfect (' + delta + 's breathing room)</span>';
  }} else if(delta > 30){{
    pacingEl.innerHTML = '<span>🎯 Pacing:</span> <span style="color:var(--cyan);font-weight:750;">Fast / Spacious (+' + delta + 's margin)</span>';
  }} else {{
    pacingEl.innerHTML = '<span>🎯 Pacing:</span> <span style="color:var(--accent);font-weight:750;">Over-Length (' + Math.abs(delta) + 's too long)</span>';
  }}
}}

// Get deduplicated sequential takes grouped logically
function getCleanSequentialTakes(){{
  const takes = [];
  let lastText = "";
  
  document.querySelectorAll('.inspector-grid .custom-input').forEach(ta => {{
    const sec = parseInt(ta.id.replace('take_', ''), 10);
    const card = ta.closest('.frame-card');
    const scene = card ? card.getAttribute('data-scene') : "1";
    const text = ta.value.trim();
    
    if(text && text !== lastText){{
      takes.push({{ second: sec, scene: scene, text: text }});
      lastText = text;
    }}
  }});
  return takes;
}}

// Build Final Assembled Voiceover Text
function buildFinalVoiceover(showFeedback = false){{
  const takes = getCleanSequentialTakes();
  const scenesMap = {{
    "1": "Scene 1 · Hook & Problem Setup",
    "2": "Scene 2 · The Realization Moment",
    "3": "Scene 3 · P.A.R.A. Method Framework",
    "4": "Scene 4 · The Engine: Dual-Agent System",
    "5": "Scene 5 · The 4-Step Workflow",
    "6": "Scene 6 · Call to Action & Closing"
  }};
  
  let md = "# 🎙️ Master Voiceover Script — WIG Animation\\n";
  md += '> Assembled from 1-second frame rewrite workbench | Total Words: ' + document.getElementById('metricWordCount').textContent + '\\n\\n';
  
  let currentScene = null;
  takes.forEach(t => {{
    if(t.scene !== currentScene){{
      currentScene = t.scene;
      const sName = scenesMap[currentScene] || ('Scene ' + currentScene);
      md += '\\n### 🎬 ' + sName + '\\n';
    }}
    const mm = Math.floor(t.second / 60);
    const ss = t.second % 60;
    const tc = mm.toString().padStart(2, '0') + ':' + ss.toString().padStart(2, '0');
    md += '\\n**[' + tc + ']** ' + t.text + '\\n';
  }});
  
  const outArea = document.getElementById('finalVoiceoverOutput');
  if(outArea){{
    outArea.value = md;
  }}
  if(showFeedback){{
    showToast("🔄 Final voiceover script re-assembled!");
  }}
}}

// Get pure voiceover text without markdown headings or timecodes
function getPureVoiceoverText(){{
  const takes = getCleanSequentialTakes();
  return takes.map(t => t.text.trim()).filter(Boolean).join('\\n\\n');
}}

// Copy full markdown script to clipboard
function copyFinalScript(){{
  const outArea = document.getElementById('finalVoiceoverOutput');
  if(!outArea) return;
  navigator.clipboard.writeText(outArea.value).then(() => {{
    showToast("📋 Copied Master Voiceover Script to clipboard!");
  }});
}}

// Copy only the spoken plain text voiceover
function copyPlainTextVO(){{
  const plain = getPureVoiceoverText();
  if(!plain){{
    showToast("No voiceover text found.");
    return;
  }}
  navigator.clipboard.writeText(plain).then(() => {{
    showToast("🎙️ Copied Plain Voiceover (Audio Only) to clipboard!");
  }});
}}

// Download plain text voiceover only (.txt)
function downloadPlainTextVO(){{
  const plain = getPureVoiceoverText();
  const blob = new Blob([plain], {{ type: 'text/plain;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = "voiceover_script.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast("📥 Downloaded voiceover_script.txt (Audio Only)");
}}

// Download Azure Object as Text File with Voiceover
async function downloadAzureVoiceoverTxt(){{
  showToast("☁️ Fetching Azure Blob voiceover object…");
  let voiceoverContent = "";
  let sourceLabel = "Azure Blob Storage (projects/aug-video-animation-1/shotlist/latest.json)";
  let retrievedAt = new Date().toISOString();

  // 1. Try to fetch the latest state directly from Azure Blob (/api/state)
  try {{
    const res = await fetch("/api/state", {{ cache: "no-store" }});
    if(res.ok){{
      const data = await res.json();
      if(data && data.ok && data.state){{
        const st = data.state;
        retrievedAt = st.savedAt || new Date().toISOString();
        if(st.finalVoiceoverScript && st.finalVoiceoverScript.trim()){{
          voiceoverContent = st.finalVoiceoverScript.trim();
        }} else if(st.voiceoverCustomTakes){{
          const lines = [];
          Object.keys(st.voiceoverCustomTakes).sort((a,b) => parseInt(a)-parseInt(b)).forEach(sec => {{
            const txt = st.voiceoverCustomTakes[sec];
            if(txt && txt.trim()){{
              const mm = Math.floor(sec/60).toString().padStart(2,'0');
              const ss = (sec%60).toString().padStart(2,'0');
              lines.push('[' + mm + ':' + ss + '] ' + txt.trim());
            }}
          }});
          voiceoverContent = lines.join('\\n\\n');
        }}
      }}
    }}
  }} catch(err){{}}

  // 2. Fallback to current assembled script if offline or API unavailable
  if(!voiceoverContent || !voiceoverContent.trim()){{
    sourceLabel = "Local Cache / State Fallback";
    voiceoverContent = document.getElementById('finalVoiceoverOutput')?.value || getPureVoiceoverText();
  }}

  // 3. Format header and payload text
  let outputTxt = "=======================================================\\n";
  outputTxt += "☁️ AZURE BLOB OBJECT VOICEOVER EXPORT\\n";
  outputTxt += "Source: " + sourceLabel + "\\n";
  outputTxt += "Blob Key: aug-video-animation-1/shotlist/latest.json\\n";
  outputTxt += "Timestamp: " + retrievedAt + "\\n";
  outputTxt += "=======================================================\\n\\n";
  outputTxt += voiceoverContent;

  const blob = new Blob([outputTxt], {{ type: 'text/plain;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = "azure_voiceover_object.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast("📥 Downloaded azure_voiceover_object.txt!");
}}

// Download storyboard as PDF (Image + Voice + Voiceover)
function downloadAsPDF(){{
  // Switch to grid view so all 200 frame cards render cleanly in PDF
  setViewMode('grid');
  
  // Make sure all textarea values are synchronized
  document.querySelectorAll('.inspector-grid .custom-input').forEach(ta => {{
    ta.textContent = ta.value;
  }});
  
  showToast("📄 Opening Print to PDF dialog… Select 'Save as PDF'");
  setTimeout(() => {{
    window.print();
  }}, 250);
}}


function scrollToFinalVO(){{
  const panel = document.getElementById('finalVoPanel');
  if(panel){{
    panel.scrollIntoView({{ behavior: 'smooth' }});
    buildFinalVoiceover(true);
  }}
}}

// Download current HTML document with all edits baked in
function downloadHTMLDoc(){{
  saveToAzure(false);
  
  // Ensure all textareas have their current values set as inner text before snapshot
  document.querySelectorAll('.inspector-grid .custom-input').forEach(ta => {{
    ta.textContent = ta.value;
  }});
  
  const htmlContent = '<!doctype html>\\n' + document.documentElement.outerHTML;
  const blob = new Blob([htmlContent], {{ type: 'text/html;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = "voiceover_inspector.html";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast("📥 Downloaded voiceover_inspector.html with all latest edits!");
}}

// Download as JSON state
function downloadJSONState(){{
  const customTakes = {{}};
  document.querySelectorAll('.inspector-grid .custom-input').forEach(ta => {{
    const sec = ta.id.replace('take_', '');
    customTakes[sec] = ta.value;
  }});
  const payload = {{
    source: "voiceover_inspector",
    totalFrames: MANIFEST_DATA.length,
    downloadedAt: new Date().toISOString(),
    takes: customTakes,
    finalScript: document.getElementById('finalVoiceoverOutput')?.value || ""
  }};
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = "voiceover_state.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast("📥 Downloaded voiceover_state.json!");
}}

// Download as markdown
function downloadScript(){{
  const text = document.getElementById('finalVoiceoverOutput').value;
  const blob = new Blob([text], {{ type: 'text/markdown;charset=utf-8' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = "master_voiceover_script.md";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast("📥 Downloaded master_voiceover_script.md");
}}

// Save to Azure Blob Storage
async function saveToAzure(manual = false){{
  const stat = document.getElementById('azureStat');
  if(stat) stat.textContent = "☁️ Saving to Azure…";
  
  const customTakes = {{}};
  document.querySelectorAll('.inspector-grid .custom-input').forEach(ta => {{
    const sec = ta.id.replace('take_', '');
    customTakes[sec] = ta.value;
  }});
  
  const payload = {{
    state: {{
      voiceoverCustomTakes: customTakes,
      finalVoiceoverScript: document.getElementById('finalVoiceoverOutput')?.value || "",
      savedAt: new Date().toISOString()
    }},
    backup: true
  }};
  
  try {{
    const res = await fetch("/api/state", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify(payload)
    }});
    if(res.ok){{
      const d = await res.json();
      const timeStr = new Date().toLocaleTimeString();
      const tag = d.versionTag ? ` (${{d.versionTag}})` : '';
      if(stat) stat.textContent = '☁️ Saved to Azure · ' + timeStr + tag;
      if(manual) showToast('☁️ Saved to Azure · ' + timeStr + tag);
    }} else {{
      if(stat) stat.textContent = "☁️ Local (Offline)";
    }}
  }} catch(err){{
    if(stat) stat.textContent = "☁️ Local (Saved)";
  }}
}}

// Filter cards by search query
function filterFrames(){{
  const q = document.getElementById('filterInput').value.toLowerCase().trim();
  document.querySelectorAll('.frame-card').forEach(card => {{
    const text = card.textContent.toLowerCase();
    card.style.display = (!q || text.includes(q)) ? "flex" : "none";
  }});
}}

// AI Voiceover Modal Controller
function openAIVoiceoverModal(){{
  const modal = document.getElementById("aiVoiceoverModal");
  if(modal) modal.style.display = "flex";
}}

function closeAIVoiceoverModal(){{
  const modal = document.getElementById("aiVoiceoverModal");
  if(modal) modal.style.display = "none";
}}

async function runAIGeneration(){{
  const prompt = document.getElementById("aiPromptInput")?.value || "";
  const statusEl = document.getElementById("aiGenStatus");
  const outputEl = document.getElementById("aiPreviewOutput");
  const btnRun = document.getElementById("btnRunAIGen");
  const btnApply = document.getElementById("btnApplyAIGen");

  if(statusEl) statusEl.textContent = "⏳ Fetching Key Vault secret & running Gemini AI...";
  if(btnRun){{
    btnRun.disabled = true;
    btnRun.textContent = "⚡ Generating with Gemini...";
  }}

  try {{
    const res = await fetch("/api/ai/generate-vo", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{ prompt: prompt, style: "resonant" }}),
    }});
    const data = await res.json();
    if(data.ok && data.script){{
      if(outputEl) outputEl.value = data.script;
      if(statusEl) statusEl.textContent = `✅ Generated via ${{data.engine}} (${{data.key_source || "Azure KV"}})`;
      if(btnApply) btnApply.style.display = "inline-flex";
    }} else {{
      if(statusEl) statusEl.textContent = `⚠️ Error: ${{data.error || "Generation failed"}}`;
    }}
  }} catch(err){{
    if(statusEl) statusEl.textContent = `❌ Network Error: ${{err.message}}`;
  }} finally {{
    if(btnRun){{
      btnRun.disabled = false;
      btnRun.textContent = "🚀 Re-Generate with Gemini AI";
    }}
  }}
}}

async function testEndpoint(engine){{
  const statusEl = document.getElementById("aiGenStatus");
  const outputEl = document.getElementById("aiPreviewOutput");
  const player = document.getElementById("aiAudioPlayer");
  const testText = "I was drowning in 46,000 notes across Obsidian.";

  if(statusEl) statusEl.textContent = `⏳ Testing ${{engine.toUpperCase()}} endpoint with first sentence...`;

  if(engine === 'gemini'){{
    try {{
      const res = await fetch("/api/ai/generate-vo", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ prompt: `Generate a 1-sentence punchy voiceover hook for: "${{testText}}"`, style: "resonant" }}),
      }});
      const data = await res.json();
      if(data.ok && data.script){{
        if(outputEl) outputEl.value = `[00:00] (Tested via ${{data.engine}})\n${{data.script}}`;
        if(statusEl) statusEl.textContent = `✅ Gemini Endpoint Verified (${{data.engine}})`;
      }} else {{
        if(statusEl) statusEl.textContent = `⚠️ Gemini Test Failed: ${{data.error}}`;
      }}
    }} catch(err){{
      if(statusEl) statusEl.textContent = `❌ Gemini Network Error: ${{err.message}}`;
    }}
  }} else {{
    // ElevenLabs or Fal.ai audio test
    try {{
      const res = await fetch("/api/ai/tts", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ engine: engine, text: testText }}),
      }});
      const data = await res.json();
      if(data.ok){{
        const audioSrc = data.audio_base64 || data.audio_url;
        if(audioSrc && player){{
          player.src = audioSrc;
          player.style.display = "block";
          player.play();
        }}
        if(outputEl) outputEl.value = `🔊 Spoken Audio Generated for:\n"${{testText}}"\n\nEngine: ${{data.engine}}\nSource: ${{data.key_source || "Azure Key Vault"}}`;
        if(statusEl) statusEl.textContent = `✅ ${{data.engine.toUpperCase()}} Audio Generated & Playing!`;
      }} else {{
        if(statusEl) statusEl.textContent = `⚠️ ${{engine}} Test Failed: ${{data.error}}`;
      }}
    }} catch(err){{
      if(statusEl) statusEl.textContent = `❌ ${{engine}} Network Error: ${{err.message}}`;
    }}
  }}
}}

async function runFalAudioGeneration(){{
  const statusEl = document.getElementById("aiGenStatus");
  const outputEl = document.getElementById("aiPreviewOutput");
  const player = document.getElementById("aiAudioPlayer");
  const btnRun = document.getElementById("btnRunFalGen");
  const testText = "I was drowning in 46,000 notes across Obsidian. So I engineered an AI knowledge engine.";

  if(statusEl) statusEl.textContent = "⏳ Generating Fal.ai audio via Azure Key Vault...";
  if(btnRun){{
    btnRun.disabled = true;
    btnRun.textContent = "⚡ Generating Fal Audio...";
  }}

  try {{
    const res = await fetch("/api/ai/tts", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{ engine: "fal", text: testText }}),
    }});
    const data = await res.json();
    if(data.ok){{
      const audioSrc = data.audio_base64 || data.audio_url;
      if(audioSrc && player){{
        player.src = audioSrc;
        player.style.display = "block";
        player.play();
      }}
      if(outputEl) outputEl.value = `⚡ Fal.ai Voiceover Audio Stream Ready!\nEngine: ${{data.engine}}\nSource: ${{data.key_source}}\nText: "${{data.text}}"`;
      if(statusEl) statusEl.textContent = `✅ Fal.ai Audio Generated successfully!`;
    }} else {{
      if(statusEl) statusEl.textContent = `⚠️ Fal.ai Error: ${{data.error}}`;
    }}
  }} catch(err){{
    if(statusEl) statusEl.textContent = `❌ Fal.ai Network Error: ${{err.message}}`;
  }} finally {{
    if(btnRun){{
      btnRun.disabled = false;
      btnRun.textContent = "⚡ Generate Audio (Fal.ai)";
    }}
  }}
}}

async function applyAIGeneratedScript(){{
  const gen = document.getElementById("aiPreviewOutput")?.value;
  if(!gen) return;
  const out = document.getElementById("finalVoiceoverOutput");
  if(out) out.value = gen;
  
  await saveToAzure(true);
  closeAIVoiceoverModal();
  showToast("🎉 Gemini AI Voiceover applied & saved to Azure Blob!");
}}

let toastTimer;
function showToast(msg){{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2400);
}}
</script>
</body>
</html>
"""
    with open(DEFAULT_HTML_DOC, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🌐 Generated Interactive HTML Inspector: {DEFAULT_HTML_DOC}")


def main():
    parser = argparse.ArgumentParser(description="Extract 1 frame per second and generate AI Voiceover rewrite workbench.")
    parser.add_argument("--video", type=str, default="", help="Path to raw exported MP4/MOV video.")
    parser.add_argument("--input-dir", type=str, default=DEFAULT_INPUT_DIR, help="Directory containing raw export video.")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Directory to save extracted frame screenshots.")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames per second to extract (default: 1.0).")
    args = parser.parse_args()

    video_path = find_target_video(args.input_dir, args.video)
    if not video_path:
        print(f"❌ No video file found in {args.input_dir}. Please place an .mp4 in {args.input_dir}/ and run again.")
        sys.exit(1)

    print(f"🎯 Target video identified: {video_path}")
    frames = extract_screenshots(video_path, args.output_dir, args.fps)
    build_manifest_and_docs(video_path, frames, args.fps)
    print("\n🎉 Done! You can now review screenshots and rewrite voiceover at:")
    print(f"   • Markdown: {DEFAULT_MD_DOC}")
    print(f"   • Interactive Inspector: {DEFAULT_HTML_DOC}")

if __name__ == "__main__":
    main()
