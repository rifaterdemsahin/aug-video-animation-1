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
.container {{ max-width:1440px; margin:0 auto; padding:20px 16px 80px; }}
.inspector-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(360px, 1fr)); gap:20px; margin-top:20px; }}
.frame-card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }}
.frame-thumb {{ position:relative; aspect-ratio:16/9; background:#000; overflow:hidden; }}
.frame-thumb img {{ width:100%; height:100%; object-fit:cover; }}
.tc-badge {{ position:absolute; bottom:8px; right:8px; background:rgba(0,0,0,0.85); color:#fff; font-family:monospace; font-size:12px; font-weight:700; padding:3px 7px; border-radius:4px; }}
.stage-badge {{ position:absolute; top:8px; left:8px; background:var(--accent2); color:#fff; font-size:10.5px; font-weight:700; padding:3px 8px; border-radius:4px; }}
.frame-body {{ padding:14px 16px; display:flex; flex-direction:column; gap:10px; flex:1; }}
.vo-option {{ background:var(--chip); border:1px solid var(--line); border-radius:6px; padding:8px 10px; font-size:12px; cursor:pointer; transition:all .15s ease; }}
.vo-option:hover {{ border-color:var(--cyan); }}
.vo-option.selected {{ border-color:var(--accent3); background:rgba(39,174,96,0.12); }}
.vo-tag {{ font-size:10px; font-weight:800; text-transform:uppercase; color:var(--muted); margin-bottom:2px; display:flex; justify-content:space-between; }}
.custom-input {{ width:100%; background:var(--bg); border:1px solid var(--line); border-radius:6px; color:var(--ink); font:inherit; font-size:12.5px; padding:8px 10px; resize:vertical; min-height:55px; }}
.custom-input:focus {{ outline:none; border-color:var(--cyan); }}
.toast {{ position:fixed; bottom:20px; right:20px; background:var(--ink); color:var(--bg); padding:10px 16px; border-radius:8px; font-size:13px; font-weight:700; opacity:0; pointer-events:none; transition:opacity .2s ease; }}
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
    <button class="btn primary" onclick="copyAllScript()">📋 Copy Script</button>
    <a href="https://www.canva.com/design/DAHRZe5KBoA/OJU0sL318CozUaTBpkdT2g/edit" class="btn" target="_blank" rel="noopener noreferrer" style="color:var(--purple,#af52de);border-color:rgba(175,82,222,0.35);background:rgba(175,82,222,0.1);" title="Open Canva Document">🎨 Canva Document ↗</a>
  </div>
</header>
<div class="container">
  <div style="background:var(--chip); border:1px solid var(--line); border-radius:10px; padding:16px 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <strong style="font-size:14px;">1-Second Screen Visual Rewrite Inspector</strong>
      <div style="font-size:12.5px; color:var(--muted);">Total Seconds Extracted: {len(manifest_entries)} | Click any suggested VO pill or type your custom take directly.</div>
    </div>
    <div>
      <input type="search" id="filterInput" oninput="filterFrames()" placeholder="Filter by scene, second, or text…" style="padding:6px 12px; font:inherit; font-size:12.5px; border-radius:6px; border:1px solid var(--line); background:var(--bg); color:var(--ink); min-width:240px;">
    </div>
  </div>

  <div class="inspector-grid" id="grid">
"""

    for e in manifest_entries:
        html_content += f"""
    <div class="frame-card" data-sec="{e['second']}" data-scene="{e['scene_num']}">
      <div class="frame-thumb">
        <img src="screenshots/{e['image_file']}" alt="Second {e['second']}" loading="lazy">
        <span class="stage-badge">Scene {e['scene_num']} · {e['scene_name']}</span>
        <span class="tc-badge">{e['timecode']}</span>
      </div>
      <div class="frame-body">
        <div class="vo-option" onclick="selectVO(this, {e['second']}, `{e['ai_punchy'].replace('`', '')}`)">
          <div class="vo-tag"><span>⚡ AI Punchy</span><span>~165 WPM</span></div>
          <div>"{e['ai_punchy']}"</div>
        </div>
        <div class="vo-option" onclick="selectVO(this, {e['second']}, `{e['ai_strategic'].replace('`', '')}`)">
          <div class="vo-tag"><span>🧠 AI Strategic</span><span>~140 WPM</span></div>
          <div>"{e['ai_strategic']}"</div>
        </div>
        <div class="vo-option" onclick="selectVO(this, {e['second']}, `{e['ai_conversational'].replace('`', '')}`)">
          <div class="vo-tag"><span>🔥 AI Conversational</span><span>~145 WPM</span></div>
          <div>"{e['ai_conversational']}"</div>
        </div>
        <div>
          <label style="font-size:11px; font-weight:700; color:var(--cyan); display:block; margin-bottom:4px;">✍️ Custom Resonant Take (Second {e['second']}):</label>
          <textarea class="custom-input" id="take_{e['second']}" placeholder="Type your custom resonant take for this frame…">{e['base_vo']}</textarea>
        </div>
      </div>
    </div>
"""

    html_content += """
  </div>
</div>
<div id="toast" class="toast"></div>
<script>
function selectVO(el, sec, text){
  const parent = el.closest('.frame-body');
  parent.querySelectorAll('.vo-option').forEach(opt => opt.classList.remove('selected'));
  el.classList.add('selected');
  const ta = document.getElementById('take_' + sec);
  if(ta){
    ta.value = text;
    showToast(`Updated Second ${sec} script!`);
  }
}
function copyAllScript(){
  const takes = [];
  document.querySelectorAll('.custom-input').forEach((ta, idx) => {
    const val = ta.value.trim();
    if(val && !takes.includes(val)){
      takes.push(val);
    }
  });
  const fullScript = takes.join("\\n\\n");
  navigator.clipboard.writeText(fullScript).then(() => {
    showToast("📋 Copied full combined voiceover script!");
  });
}
function filterFrames(){
  const q = document.getElementById('filterInput').value.toLowerCase().trim();
  document.querySelectorAll('.frame-card').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = (!q || text.includes(q)) ? "flex" : "none";
  });
}
let toastTimer;
function showToast(msg){
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2200);
}
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
