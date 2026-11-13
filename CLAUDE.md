# japan-archive-video-factory — notes for Claude

Read `docs/HANDOVER.md` first (the owner, their standing decisions, the current state), then `AGENT_ARC.md` (how a
video is made) and `00-video-mau/HUONG-DAN-EDIT.md` (the owner's editing guide for the approved sample). The owner is
Vietnamese and not technical: answer in short, simple Vietnamese, no jargon.

This repo makes one thing: vertical Japanese history and legend shorts from real archive documents (excavation
photos, artefacts, maps, scans, old engravings and paintings), a Japanese voice and subtitles timed to it, laid out
as the approved Göbekli Tepe sample (`00-video-mau/MAU-EDIT-20S.mp4`). One issue `[Lịch sử] …` = one video; the
machine steps run on GitHub Actions (`arc.yml`), Claude's steps are in `AGENT_ARC.md`. It is built on the same
design as `maihaianh2911-bit/japan-video-factory` (literature videos), which runs independently. The owner's shared
Claude task (the one of `japan-video-factory`) does Claude's steps unattended when GitHub calls it after each
machine step (entry: `AGENT_NIGHTLY.md`), or this repo's own task when each repo has its own Claude seat (its
prompt: "Làm theo AGENT_NIGHTLY.md của repo maihaianh2911-bit/japan-archive-video-factory."); either needs the
secrets `CLAUDE_TASK_URL` and `CLAUDE_TASK_TOKEN` in this repo. There is no hourly run (owner, 13/11/2026); if a
call is missed (usage limit), the button "Gọi Claude ngay" (`wake.yml`) starts it.

## When you were started by GitHub (a Claude task, nobody in the chat)
The prompt may be as short as "Làm việc đang chờ trong repo này" ("do the work waiting in this repo"), and GitHub
adds a line such as "Phiếu lịch sử số 3: giọng và ảnh đã sẵn sàng, chờ chọn ảnh". Then: follow `AGENT_NIGHTLY.md`
of this repo (its first check lists the `arc-*` issues waiting for you), then `AGENT_ARC.md`. Nobody answers
questions, so do not ask; comments go on the issues (🤖, Vietnamese).

## When the owner pastes a script in a chat
1. Create one issue in `maihaianh2911-bit/japan-archive-video-factory`: title `[Lịch sử] <Japanese title> —
   <main idea>`, body with the sections of `docs/CHATGPT.md` (Chủ đề / Kịch bản = the script exactly as pasted /
   Giọng đọc `clone_190 — kể chuyện (mặc định)` / Ghi chú = wishes from the chat). No labels: the workflow adds them.
2. Right after creating the issue, add `arc-busy` to it: opening the issue wakes the Claude task at once, and the
   label tells it the issue is taken (`AGENT_ARC.md` §0). Keep `arc-busy` while you work and wait in the chat (the
   task, woken after each machine step, then leaves the issue to you; the claim counts for 2 hours from when the
   label was added, so remove and add it again on a longer chat). Do Claude's steps of `AGENT_ARC.md` for that issue
   right away instead of waiting for the task: `script.json` → wait for the voice and pictures (~15–25 min) →
   `picks.json`, with the framing preview → wait for the render (~10–20 min) → check the shot sheet → closing
   comment, then remove `arc-busy`. While a machine step runs, say so in one line and wait; if the owner does not
   want to wait, stop right after one of your pushes (while a machine step runs) and remove `arc-busy`: the Claude
   task continues from the labels when GitHub calls it after that step.
3. Give the owner the links to the video (view + download), the subtitles and the picture credits.

Quality first: look at every picture yourself, preview the framing and rings before rendering.

## Changing the pipeline
Before pushing to `main`: `python3 tests/arc_smoke.py --still`, `python3 -m compileall -q scripts tests`,
`npm run check`. Never touch secrets. Comments posted on GitHub start with 🤖 (they come from the owner's account).
No pull requests unless asked. The session cannot delete branches or tags.
