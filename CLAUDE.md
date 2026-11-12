# japan-archive-video-factory — notes for Claude

Read `docs/HANDOVER.md` first (the owner, their standing decisions, the current state), then `AGENT_ARC.md` (how a
video is made) and `00-video-mau/HUONG-DAN-EDIT.md` (the owner's editing guide for the approved sample). The owner is
Vietnamese and not technical: answer in short, simple Vietnamese, no jargon.

This repo makes one thing: vertical Japanese history and legend shorts from real archive documents (excavation
photos, artefacts, maps, scans, old engravings and paintings), a Japanese voice and subtitles timed to it, laid out
as the approved Göbekli Tepe sample (`00-video-mau/MAU-EDIT-20S.mp4`). One issue `[Lịch sử] …` = one video; the
machine steps run on GitHub Actions (`arc.yml`), Claude's steps are in `AGENT_ARC.md`. It is built on the same
design as `maihaianh2911-bit/japan-video-factory` (literature videos), which runs independently.

## When the owner pastes a script in a chat
1. Create one issue in `maihaianh2911-bit/japan-archive-video-factory`: title `[Lịch sử] <Japanese title> —
   <main idea>`, body with the sections of `docs/CHATGPT.md` (Chủ đề / Kịch bản = the script exactly as pasted /
   Giọng đọc `clone_190 — kể chuyện (mặc định)` / Ghi chú = wishes from the chat). No labels: the workflow adds them.
2. Do Claude's steps of `AGENT_ARC.md` for that issue right away instead of waiting for the hourly run (claim with
   `arc-busy` as written there): `script.json` → wait for the voice and pictures (~10 min) → `picks.json`, with
   the framing preview → wait for the render (~10–20 min) → check the shot sheet → closing comment. While a machine
   step runs, say so in one line and wait; if the owner does not want to wait, stop after any step: the hourly
   routine continues from the labels.
3. Give the owner the links to the video (view + download), the subtitles and the picture credits.

Quality first: look at every picture yourself, preview the framing and rings before rendering.

## Changing the pipeline
Before pushing to `main`: `python3 tests/arc_smoke.py --still`, `python3 -m compileall -q scripts tests`,
`npm run check`. Never touch secrets. Comments posted on GitHub start with 🤖 (they come from the owner's account).
No pull requests unless asked. The session cannot delete branches or tags.
