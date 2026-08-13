# August Video Animation #1

Public workbench for a 2:58 animated film: **AI Second Brain**.

I am turning a Canva production plan into a YouTube/LinkedIn video — shotlist, voiceover, stills, and 26 Google Flow clips. This repo is the production, not the finished cut.

**Live:** [rifaterdemsahin.github.io/aug-video-animation-1](https://rifaterdemsahin.github.io/aug-video-animation-1/)

## Open

| Path | What |
|------|------|
| [index.html](index.html) | Public landing — what I am doing, one playable clip |
| [storyboard.html](storyboard.html) | Browser shotlist (scenes, VO, tags, Flow players) |
| [_script.md](_script.md) | Flagship VO (Part A) + stage walkthrough (Part B) |
| [stills/images_manifest.json](stills/images_manifest.json) | Catalog of every still (paths, stage, caption) |
| [video_flow/video_flow_manifest.json](video_flow/video_flow_manifest.json) | Catalog of the 26 Flow clips |

Landing page and shotlist share a **dark / light** toggle (saved in this browser). Default follows the OS.

Local extras: `python3 server.py` on port 8765 for OpenRouter grammar/rewrite and vault path search. Then open [http://127.0.0.1:8765/storyboard.html](http://127.0.0.1:8765/storyboard.html). Static GitHub Pages does not run that API.

## Layout

```
.
├── index.html              public landing (GitHub Pages)
├── storyboard.html         shotlist editor
├── _script.md              voiceover seed
├── server.py               local shotlist server + /api/*
├── stills/                 Canva / production stills, by stage
│   ├── images_manifest.json
│   ├── 00_index/
│   ├── 01_architecture/
│   ├── 02_plan/            script source deck (20 slides)
│   ├── 03_assets/
│   ├── 04_cohort/
│   ├── 05_gaps/
│   ├── 06_assembly/
│   ├── 07_polish/
│   ├── 08_refinement/
│   ├── 09_audio/
│   ├── 10_editcolor/
│   ├── 11_thumbnail/
│   ├── 12_export/
│   ├── 13_metadata/
│   └── 15_tactics/
└── video_flow/             26 Google Flow MP4s
    ├── NN_descriptive-slug.mp4
    ├── _first_frames/      frame 0 stills (posters)
    └── video_flow_manifest.json
```

Stage 14 (WIG / my story) has no still yet — the VO lives in `_script.md` Part B.

## Stills

Each still lives at `stills/{stage}_{name}/{filename}.png`. The shotlist loads those paths from `stills/images_manifest.json` (also inlined in `storyboard.html`). Saved browser state that still points at the old root filenames is remapped on load.

| Folder | Stage | Files |
|--------|-------|------:|
| [stills/00_index/](stills/00_index/00_index.png) | 00 Index | 1 |
| [stills/01_architecture/](stills/01_architecture/01_architecture.png) | 01 Architecture | 1 |
| [stills/02_plan/](stills/02_plan/02_plan_00_cover-title.png) | 02 Plan | 20 |
| [stills/03_assets/](stills/03_assets/03_assets_00_ref-google-flow.png) | 03 Assets | 57 |
| [stills/04_cohort/](stills/04_cohort/04_cohort_00_week7-notes.png) | 04 Cohort | 3 |
| [stills/05_gaps/](stills/05_gaps/05_gaps_00_hallucination-vs-context.png) | 05 Gaps | 9 |
| [stills/06_assembly/](stills/06_assembly/06_assembly_00_scene1-2-stills.png) | 06 Assembly | 2 |
| [stills/07_polish/](stills/07_polish/07_polish_00_divider-empty.png) | 07 Polish | 1 |
| [stills/08_refinement/](stills/08_refinement/08_refinement_00_divider-empty.png) | 08 Refinement | 1 |
| [stills/09_audio/](stills/09_audio/09_audio_00_divider-empty.png) | 09 Audio | 1 |
| [stills/10_editcolor/](stills/10_editcolor/10_editcolor_00_divider-empty.png) | 10 Edit Color | 1 |
| [stills/11_thumbnail/](stills/11_thumbnail/11_thumbnail_00_divider-empty.png) | 11 Thumbnail | 1 |
| [stills/12_export/](stills/12_export/12_export_00_divider-empty.png) | 12 Export | 1 |
| [stills/13_metadata/](stills/13_metadata/13_metadata_00_template-empty.png) | 13 Metadata | 2 |
| [stills/15_tactics/](stills/15_tactics/15_tactics_00_editor-screenshot-stub.png) | 15 Tactics | 4 |

## Video Flow

Clips stay in `video_flow/`, named `NN_first-frame-slug.mp4`. First-frame posters are `video_flow/_first_frames/NN_first-frame-slug.jpg`. The shotlist plays them on Stage 16.

Example: [video_flow/18_golden-brain-lightning.mp4](video_flow/18_golden-brain-lightning.mp4)

## Run locally

```bash
python3 server.py
# open http://127.0.0.1:8765/          → index.html
#      http://127.0.0.1:8765/storyboard.html
```

Grammar / rewrite on a shot's VO and `[[` vault path search need this server. Everything else is static and works on GitHub Pages.

By [Rifat Erdem Sahin](https://github.com/rifaterdemsahin) / DeliveryPilot.
