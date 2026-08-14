---
title: WIG Animation — Voiceover Script
date: 2026-08-11
tags: [project, video, wiganimation, script]
status: draft
---

# WIG Animation — Voiceover Script

Editable from the storyboard page (`research.html` at the repo root) — that page loads this
structure into a textarea, shows live word count / marked-slide count, and saves your latest
edits to browser storage. This file is the seed copy; after editing in the browser, use its
"Download .md" button and overwrite this file to keep it in sync.

Two layers, on purpose:
1. **Flagship script (Part A)** — the fully-written, ready-to-record 2:58 "AI Second Brain"
   video script that was already drafted inside the Canva planning deck (`stills/02_plan/`).
   Nothing invented — transcribed as-is.
2. **Framework walkthrough (Part B)** — a stage-by-stage (00–15) narration matched to the
   renamed image order, for a behind-the-scenes / process video that tours the whole
   production framework, including a new **Stage 14 — WIG** scene built from your real
   career story (found via vault search, not fabricated — see source note below Stage 14).

Use whichever layer fits the cut you're actually making, or splice A into B's Stage 02 beat.

---

## Part A — Flagship script: "AI Second Brain" (2:58, 6 scenes)

**Source**: `stills/02_plan/02_plan_00_cover-title.png` through `stills/02_plan/02_plan_19_music-audio.png`. Voice tone:
energetic/direct → thoughtful/strategic → instructor → motivational. Pace 140–160 wpm, ~475 words.

### Scene 1 — Hook & Problem Setup [0:00–0:15]
> "I was drowning in 46,000 notes across Obsidian. Every search felt like looking for a needle
> in a digital haystack. And then I realized—the problem wasn't the number of notes. It was
> that they weren't **working for me**."

*Animation*: chaotic dark workspace, glowing vault icon swirled by 46,000 note-icons, glitch
effects, red accent (#e74c3c), zoom to red-X transition. Candidate stills: `stills/06_assembly/06_assembly_00_scene1-2-stills.png`.

### Scene 2 — The Realization Moment [0:15–0:45]
> "So I engineered something different: a machine-readable, AI-native knowledge engine. No
> more chaos. No more manual digging. Instead, I built a system where AI agents can query,
> synthesize, and update my entire knowledge base—automatically. And here's the best part:
> it's designed to prepare you for modern AI certifications, like the Claude Certified
> Architect Professional exam."

*Animation*: vault icon glows gold, 46,000 notes snap into four P.A.R.A. zones (Projects
#e74c3c, Areas #3498db, Resources #27ae60, Archive #95a5a6).

### Scene 3 — P.A.R.A. Method Framework [0:45–1:20]
> "The foundation is the P.A.R.A. method—four zones that AI understands instantly:
> **Projects**—short-term efforts with deadlines. **Areas**—long-term responsibilities you
> own. **Resources**—reference material and topics of interest. And **Archive**—everything
> inactive. Why this works: AI agents can navigate structured vaults 100x faster than messy
> folders. Imagine your knowledge base talking back to you."

*Animation*: split-screen carousel, 4 zones in sequence (5–7s dwell each), icon-driven.
Reference: `stills/03_assets/03_assets_01_para-vault-counts.png` (real live note counts).

### Scene 4 — The Engine: Dual-Agent System [1:20–1:55]
> "Then comes the engine: a local dual-agent rig running Gemini and Claude in tandem. While
> you're working, these agents are running in the background—syncing across GitHub, Google
> Drive, Proxmox. Generating changelogs. Maintaining structure. You focus on execution. They
> handle the busywork. It's automation that actually scales."

*Animation*: terminal `localhost:8899`, two agent avatars (Gemini gold, Claude blue)
exchanging data, streams to GitHub/Drive/Proxmox/Vault icons, sync % bottom-right.
Reference: `stills/03_assets/03_assets_02_dashboard-screenshot.png` (real dashboard).

### Scene 5 — The 4-Step Workflow [1:55–2:25]
> "Raw knowledge isn't power—**applied** knowledge is. So I built a 4-step workflow: **Tell**
> your thoughts into Obsidian. Brain-dump raw context. **Show** concepts visually in
> Canva—map relationships, refine structure. **Do**—turn that into slides and presentations.
> Make it consumable. **Apply**—ship it as code, assets, or implementations in GitHub. From
> chaos to execution in four steps."

*Animation*: 4 boxes left-to-right — Tell (purple #9b59b6), Show (orange #e67e22), Do (red
#c0392b), Apply (green #27ae60) — arrows + checkmarks between steps.

### Scene 6 — Call to Action & Closing [2:25–2:58]
> "This isn't just about note-taking anymore. It's about building a second brain that
> actually **works for you**. And if you're serious about AI skills—whether you're prepping
> for certifications or just want to think faster—this system accelerates everything. We're
> launching a hands-on cohort where you'll build this from scratch, master the framework, and
> unlock real AI execution skills. Links in the comments. Let's go."

*Animation*: brain+lightning icon, orbiting cert/vault/GitHub/YouTube/Canva icons, gold pulse,
"Build Your AI Second Brain" → "Join the Hands-On Cohort" → "Links in the comments ↓".
Reference: `stills/04_cohort/04_cohort_02_schedule.png` (real: every Sunday, 9–11PM UK, free).

**Delivery notes**: Opening energy 6/10 conversational · Framework 7/10 instructor tone · Workflow
8/10 building momentum, chant "Tell...Show...Do...Apply" · CTA 9/10, "Let's go" as invitation not
command. ElevenLabs: Multilingual v2, Voice Thomas/Aria, rate 1.0x, stability 0.75–0.85, similarity
0.8. Pronunciation: Obsidian "ob-SID-ee-un", P.A.R.A. "PAR-uh", Gemini "JEM-uh-nee", Proxmox
"PROKS-moks", CCAR-P "See-car-P".

**Tech specs**: 1920×1080, 30fps (or 60fps), H.264 8–12Mbps, AAC 128kbps+, sRGB. Fonts: Inter Bold
(headlines), Roboto/Montserrat (body), Courier New/Inconsolata (code). Full palette: bg #0a0a0f,
UI #1a1a2e, red #e74c3c, blue #3498db, green #27ae60, gray #95a5a6, gold #f39c12, text #ecf0f1.

---

## Part B — Framework walkthrough (Stage 00–15, matched to renamed image order)

Short narration beats, one per production stage, for a behind-the-scenes cut that tours the
whole `WIGAnimation` framework itself. Mark the ones you actually want voiced in
`research.html`; the rest can stay silent B-roll with on-screen text only.

### 00 — Index
> "Every video I make now runs through the same sixteen-step pipeline. This is the map."

### 01 — Architecture
> "Plan. Assets. Assembly. Polish. Publish. Each stage has one job, and one tool that does it."

### 02 — Plan
> "The plan isn't a vibe — it's a script, timed to the second, with the animation prompt for
> every scene written before I generate a single frame." *(→ splice in Part A here if doing the
> full flagship cut.)*

### 03 — Assets
> "46,000 notes, 210 live projects — the numbers on screen aren't mockups. That's my actual
> second brain, queried live."

### 04 — Cohort
> "Every Sunday, 9 to 11PM UK time, free — I open my screen and we push AI to its limits
> together. No experience required. That's not a tagline, that's Week 7's calendar invite."

### 05 — Gaps
> "The gap is context. Low-context AI hallucinates. Feed it your history, your preferences,
> your own archive — and it stops guessing and starts knowing you."

### 06 — Assembly
> "This is where the script and the first generated stills meet — chaos and clarity, side by
> side, before they ever hit a timeline."

### 07 — Polish
> "Every cut gets a pass in DaVinci before it's allowed to move on."

### 08 — Refinement
> "Refinement is where I cut what doesn't earn its seconds."

### 09 — Audio
> "Voiceover at minus six, music bed at minus eighteen to minus twenty-four — score it so the
> words never fight the track."

### 10 — Edit Color
> "Color and graphics last, once the timing already works — never the other way round."

### 11 — Thumbnail
> "The thumbnail gets the same AI pipeline as everything else: generated, not stock."

### 12 — Export
> "1080p, H.264, 8 to 12 megabits. One export setting, every time, so nothing downstream breaks."

### 13 — Metadata
> "Title, description, tags — written by the same system that wrote the script, then reviewed
> by me before it ships."

### 14 — WIG — My Story
*This stage was explicitly marked "reserved for future expansion" in the framework diagram —
no image existed for it. This is that expansion: the real Wildly Important Goal behind the
whole framework, sourced from your Skool bio (`3_Resources_Constraints/personal/rifat-erdem-sahin-skool-bio.md`),*
*not invented.*

> "For twenty years I was the SRE who fixed things by hand — critical national infrastructure,
> National Grid, Goldman Sachs, Microsoft. Forty-plus enterprise projects, cleared for the work
> that can't fail. Then the game changed. I stopped writing more scripts and started building
> agentic operational models — Claude, Qdrant, n8n — systems that see drift and fix themselves
> before I wake up. That's my Wildly Important Goal: from a manual, bottlenecked SRE, to an
> agentic, self-remediating way of working, by teaching ten thousand people to build the same
> thing. That's Delivery Pilot. This whole framework is that goal, running."

*No slide exists for this stage yet — mark it voiceover-important in the storyboard page anyway,
and either cut a new title card ("WIG: From X to Y by When") or run it under Scene 1's chaos
visual as a cold open.*

### 15 — Tactics
> "Tactics are the small, unglamorous reps — the actual hands-on-keyboard work that makes the
> other fifteen steps real."

---

## Production checklist (from `stills/02_plan/02_plan_17_checklist.png`)
- [ ] Script reviewed aloud, timed to 2:58
- [ ] Voice practice — tone shifts rehearsed
- [ ] ElevenLabs set up (voice, stability, similarity)
- [ ] Animation prompts reviewed against CSV (`stills/02_plan/02_plan_18_csv-master.png`)
- [ ] Audio levels checked (-12dB peak)
- [ ] Timing sync verified against the 6-scene table
- [ ] Color consistency across scenes (master palette)
- [ ] Text readability (16pt+)
- [ ] Final export: H.264, 1920×1080, 30fps, 8–12Mbps, AAC
- [ ] Subtitles / SRT
- [ ] Thumbnail (1280×720)
- [ ] Title, description, tags, YouTube chapters
