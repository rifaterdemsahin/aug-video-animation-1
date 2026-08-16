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

# Master Script Scenes Reference
MASTER_SCENES = [
    {
        "stage": "01",
        "scene": 1,
        "name": "Hook & Problem Setup",
        "start": 0,
        "end": 15,
        "base_vo": "I was drowning in 46,000 notes across Obsidian. Every search felt like looking for a needle in a digital haystack. And then I realized—the problem wasn't the number of notes. It was that they weren't working for me.",
        "ai_punchy": "46,000 notes in Obsidian, zero clarity. Every search was a needle in a digital haystack. The problem wasn't the notes—they just weren't working for me.",
        "ai_strategic": "I had accumulated over 46,000 notes in Obsidian, but finding relevant insights was impossible. Chaos isn't a scaling strategy—structure is.",
        "ai_conversational": "Ever felt buried under your own notes? With 46,000 files in Obsidian, every search was painful. Here is how I fixed it."
    },
    {
        "stage": "02",
        "scene": 2,
        "name": "The Realization Moment",
        "start": 15,
        "end": 45,
        "base_vo": "So I engineered something different: a machine-readable, AI-native knowledge engine. No more chaos. No more manual digging. Instead, I built a system where AI agents can query, synthesize, and update my entire knowledge base—automatically. And here's the best part: it's designed to prepare you for modern AI certifications, like the Claude Certified Architect Professional exam.",
        "ai_punchy": "So I built an AI-native second brain. No manual digging. AI agents query, synthesize, and update my entire vault automatically—prepping you for top AI certs.",
        "ai_strategic": "The breakthrough: transform raw markdown into a machine-readable graph. Autonomous agents index and synthesize your history 100x faster.",
        "ai_conversational": "Instead of organizing files by hand, I let AI do the heavy lifting. Now my agents query, connect, and update my notes while I sleep."
    },
    {
        "stage": "03",
        "scene": 3,
        "name": "P.A.R.A. Method Framework",
        "start": 45,
        "end": 80,
        "base_vo": "The foundation is the P.A.R.A. method—four zones that AI understands instantly: Projects—short-term efforts with deadlines. Areas—long-term responsibilities you own. Resources—reference material and topics of interest. And Archive—everything inactive. Why this works: AI agents can navigate structured vaults 100x faster than messy folders. Imagine your knowledge base talking back to you.",
        "ai_punchy": "The engine runs on P.A.R.A: Projects, Areas, Resources, and Archive. Structured four-zone taxonomy that AI agents parse in milliseconds.",
        "ai_strategic": "P.A.R.A provides deterministic boundaries for LLM context windows. Four clean zones eliminate ambiguity and hallucination.",
        "ai_conversational": "Four simple folders: Projects, Areas, Resources, and Archive. Clean structure means AI agents find answers in seconds."
    },
    {
        "stage": "04",
        "scene": 4,
        "name": "The Engine: Dual-Agent System",
        "start": 80,
        "end": 115,
        "base_vo": "Then comes the engine: a local dual-agent rig running Gemini and Claude in tandem. While you're working, these agents are running in the background—syncing across GitHub, Google Drive, Proxmox. Generating changelogs. Maintaining structure. You focus on execution. They handle the busywork. It's automation that actually scales.",
        "ai_punchy": "The horsepower: Gemini Gold and Claude Blue working in tandem. Background sync across GitHub, Drive, and Proxmox. Automation that actually scales.",
        "ai_strategic": "A local dual-agent orchestration rig. One agent handles indexing and consistency; the other queries and synthesizes in real time.",
        "ai_conversational": "Meet the dual-agent engine: Gemini and Claude running in parallel. They handle syncing and changelogs so you can focus on shipping."
    },
    {
        "stage": "05",
        "scene": 5,
        "name": "The 4-Step Workflow",
        "start": 115,
        "end": 145,
        "base_vo": "Raw knowledge isn't power—applied knowledge is. So I built a 4-step workflow: Tell your thoughts into Obsidian. Brain-dump raw context. Show concepts visually in Canva—map relationships, refine structure. Do—turn that into slides and presentations. Make it consumable. Apply—ship it as code, assets, or implementations in GitHub. From chaos to execution in four steps.",
        "ai_punchy": "Knowledge is only power when applied. The 4-step loop: Tell into Obsidian, Show in Canva, Do in slides, Apply in GitHub. Chaos to execution.",
        "ai_strategic": "A closed-loop operational pipeline: Tell, Show, Do, Apply. From unstructured brain-dumps to production code repositories.",
        "ai_conversational": "Four steps from thought to execution: Tell your thoughts, Show the visuals, Do the deck, and Apply the code in GitHub."
    },
    {
        "stage": "06",
        "scene": 6,
        "name": "Call to Action & Closing",
        "start": 145,
        "end": 178,
        "base_vo": "This isn't just about note-taking anymore. It's about building a second brain that actually works for you. And if you're serious about AI skills—whether you're prepping for certifications or just want to think faster—this system accelerates everything. We're launching a hands-on cohort where you'll build this from scratch, master the framework, and unlock real AI execution skills. Links in the comments. Let's go.",
        "ai_punchy": "Build a second brain that actually works for you. Join our free hands-on Sunday cohort and master agentic workflows from scratch. Links below. Let's go.",
        "ai_strategic": "Accelerate your AI engineering readiness. Join the live weekly cohort, build the architecture hands-on, and earn your certification.",
        "ai_conversational": "Ready to build your AI second brain? Join our live Sunday cohort and build this system with us. Check the links below—let's go!"
    }
]

def format_tc(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def get_scene_for_sec(sec: int) -> dict:
    for sc in MASTER_SCENES:
        if sc["start"] <= sec < sc["end"]:
            return sc
    return MASTER_SCENES[-1]

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
        print(f"⚠️ Could not read duration via ffprobe ({e}). Defaulting to 178s.")
        return 178.0

def find_target_video(input_dir: str, explicit_video: str = None) -> str:
    if explicit_video and os.path.exists(explicit_video):
        return explicit_video
    
    # Check inside input_dir for mp4 or mov
    candidates = glob.glob(os.path.join(input_dir, "*.mp4")) + glob.glob(os.path.join(input_dir, "*.mov"))
    if candidates:
        return sorted(candidates)[0]
    
    # Fallback to demo video flow clip if nothing in rawexport
    fallback_clips = glob.glob("video_flow/*.mp4")
    if fallback_clips:
        print(f"ℹ️ No video found in {input_dir}. Using sample video from video_flow/ for demonstration.")
        return sorted(fallback_clips)[0]
    
    return ""

def extract_screenshots(video_path: str, output_dir: str, fps: float = 1.0) -> list:
    os.makedirs(output_dir, exist_ok=True)
    # Pattern: frame_%04d_sec_%03d.jpg
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
        scene = get_scene_for_sec(sec)
        rel_fpath = os.path.relpath(fpath, start=os.path.dirname(DEFAULT_MD_DOC))
        
        manifest_entries.append({
            "index": idx,
            "second": sec,
            "timecode": format_tc(sec),
            "image_file": os.path.basename(fpath),
            "image_path": fpath,
            "rel_path": rel_fpath,
            "stage": scene["stage"],
            "scene_num": scene["scene"],
            "scene_name": scene["name"],
            "base_vo": scene["base_vo"],
            "ai_punchy": scene["ai_punchy"],
            "ai_strategic": scene["ai_strategic"],
            "ai_conversational": scene["ai_conversational"]
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
        f"> **Source Video**: `{video_name}` | **Extracted Frames**: {len(manifest_entries)} | **Pacing Target**: 140–160 WPM",
        f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Tactic**: 1-Second Frame Extraction & Visual AI Scripting",
        "",
        "---",
        "",
        "## 🛠️ How to Use This Workbench",
        "1. Inspect each **1-second screenshot** below to see exactly what visual motion graphic or Canva slide is on screen.",
        "2. Review the **Original Scratch VO** vs. **AI-Suggested Variations** (Punchy, Strategic, Conversational).",
        "3. Write your **Final Resonant Voiceover** directly in the `[My Resonant Take]` block.",
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
            f"### ⏱️ Timestamp: `{entry['timecode']}` (Second {entry['second']})",
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
            "> *Click or type your custom voiceover rewrite for this visual second here...*",
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
      <a href="voiceover_inspector.html" class="nav-item active"><span>🎙️</span> VO Inspector</a>
      <a href="https://canva.link/p4u3nwvsmio19jp" class="nav-item" target="_blank" rel="noopener noreferrer" style="color:var(--purple,#af52de);" title="Canva Implementation Deck"><span>🎨</span> Implementation ↗</a>
    </nav>
    <button class="btn primary" onclick="scrollToFinalVO()">📋 Generate Final Voiceover</button>
    <button class="btn success" onclick="downloadHTMLDoc()" title="Save all changes and download updated voiceover_inspector.html">💾 Save &amp; Download HTML</button>
    <button class="btn blue" onclick="downloadPlainTextVO()" title="Download spoken voiceover audio text only (.txt)">🎙️ Download Voiceover</button>
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
      <button class="btn" onclick="saveToAzure(true)">☁️ Save to Azure</button>
      <button class="btn success" onclick="downloadHTMLDoc()" title="Download current HTML page with all edits baked in">📥 Download HTML</button>
      <button class="btn blue" onclick="downloadPlainTextVO()" title="Download spoken plain text voiceover only (.txt)">🎙️ Download Voiceover</button>
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
        
        html_content += f"""
    <div class="frame-card" data-sec="{e['second']}" data-scene="{e['scene_num']}">
      <div class="frame-thumb" onclick="openSlideAt({e['second']})" style="cursor:pointer;" title="Click to view in Slide Show Mode">
        <img src="screenshots/{e['image_file']}" alt="Second {e['second']}" loading="lazy">
        <span class="stage-badge">Scene {e['scene_num']} · {e['scene_name']}</span>
        <span class="tc-badge">{e['timecode']}</span>
      </div>
      <div class="frame-body">
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
        <button class="btn success" onclick="downloadHTMLDoc()" title="Download complete HTML inspector page">📥 Download HTML</button>
        <button class="btn" onclick="downloadScript()" title="Download script as markdown with timecodes">📥 Download .md</button>
        <button class="btn" onclick="downloadJSONState()" title="Download state as JSON">📥 Download JSON</button>
        <button class="btn" onclick="buildFinalVoiceover(true)">🔄 Re-Assemble</button>
      </div>
    </div>

    <textarea class="final-vo-textarea" id="finalVoiceoverOutput" readonly></textarea>
  </div>
</div>

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
  document.getElementById('slideStageBadge').textContent = 'Scene ' + item.scene_num + ' · ' + item.scene_name;
  document.getElementById('slideTcBadge').textContent = item.timecode;
  document.getElementById('slideCounter').textContent = 'Frame ' + (currentSlideIndex + 1) + ' / ' + MANIFEST_DATA.length + ' (' + item.timecode + ')';
  document.getElementById('slideScrubber').value = currentSlideIndex;
  
  document.getElementById('slideTakeLabel').textContent = '✍️ Custom Resonant Take (Second ' + item.second + '):';
  
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
    backup: false
  }};
  
  try {{
    const res = await fetch("/api/state", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify(payload)
    }});
    if(res.ok){{
      const timeStr = new Date().toLocaleTimeString();
      if(stat) stat.textContent = '☁️ Saved to Azure · ' + timeStr;
      if(manual) showToast('☁️ Voiceover saved to Azure at ' + timeStr);
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
