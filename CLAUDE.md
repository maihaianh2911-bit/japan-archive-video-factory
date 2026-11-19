# japan-archive-video-factory — notes for Claude

## Iron rules (owner, 16/11/2026) — they come before everything else in this file
1. **The video is in the channel's language: Japanese (tiếng Nhật).** The voice is the channel's Japanese voice (`clone_190` by default), and the script lines, subtitles and
   on-screen text are in Japanese (tiếng Nhật). A script that arrives in another language is translated faithfully into Japanese (tiếng Nhật)
   first. Never a voice or text of another language: check the language of `lines` and the voice before the voice
   step, and again on the finished video. A video in the wrong language is not delivered: fix it and render again.
2. **No video under 60 seconds.** Before the voice step, estimate the length from the script (use the seconds per
   line of this channel's earlier videos); after the voice step, read the real length of the speech (the machine
   comment gives it). If the video would be under 60 seconds, **write the script longer** (more true facts and
   detail on the same subject, in the owner's tone, nothing invented) until it passes 60 seconds, tell the owner on
   the issue what was added, and only then go on. This is the one exception to "never change the owner's script".
   Never render or deliver a video under 60 seconds. Only exception: a trial or sample video — the owner says so,
   or the issue title or notes say `thử`, `mẫu`, `test` or `demo`.
3. **Every video is vertical (1080×1920) and 80–160 seconds long** (owner, 18/11/2026: "tất cả các kênh đều làm
   dạng dọc, 80-160s thôi"). Write the script for that length: under 80 s add true scenes and details of the same
   story (never padding), over 160 s cut repetition. Trial or sample videos are the exception, as in rule 2.

Read `docs/HANDOVER.md` first (the owner, their standing decisions, the current state), then `AGENT_ARC.md` (how a
video is made) and `00-video-mau/HUONG-DAN-EDIT.md` (the owner's editing guide for the approved sample). The owner is
Vietnamese and not technical: answer in short, simple Vietnamese, no jargon.

Since 18/11/2026 it also makes `[Truyền thuyết]` videos: Japanese urban legends and horror stories, one story per
video, pictures from the whole web (film stills allowed, credited), no AI pictures, written and shown as the owner
approved on issue 12 (`AGENT_ARC.md` §5: the script in one unbroken explainer flow, a hook shared by the series, an
ending that leads to the next video, the `horror` look). In a chat: the owner approves the script first, then a
20-second trial for a new series or look, then the full render. When the owner says stop, stop.

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
   label tells it the issue is taken (`AGENT_ARC.md` §0). Keep `arc-busy` while you work and wait in the chat (while
   the label is under 2 hours old the machine does not call the task for this issue, and a task leaves it to you;
   the claim counts for 2 hours from when the label was added, so remove and add it again on a longer chat). Do Claude's steps of `AGENT_ARC.md` for that issue
   right away instead of waiting for the task: `script.json` → wait for the voice and pictures (~10–25 min; 13 min for 19 lines) →
   `picks.json`, with the framing preview → wait for the render (~4–10 min; 4–5 min for a 1-minute video) → check the shot sheet → closing
   comment, then remove `arc-busy`. While a machine step runs, say so in one line and wait; if the owner does not
   want to wait, stop right after one of your pushes (while a machine step runs) and remove `arc-busy`: the Claude
   task continues from the labels when GitHub calls it after that step.
3. Give the owner the links to the video (view + download), the subtitles, the posting caption (`caption.txt`,
   written by Claude at the picks step, owner 16/11/2026) and the picture credits.

Iron rule (owner, 16/11/2026): **no video under 60 s** — under 60 s nothing is rendered (`build.py` refuses); write
80–160 s (iron rule 3; `AGENT_ARC.md` §1). Quality first: look at every picture yourself, preview the framing and rings before rendering.

## A video the owner sends (owner, 19/11/2026, for every repo)
"nếu repo nào đc dựng bằng cách remix video hoặc tao có gửi video, có thể sử dụng hình ảnh/video trong video tao gửi":
when a video of this repo is made from a video the owner sent (a remix, or a video sent in the chat), **the pictures
and the footage of that video may be used** in ours, beside the pictures of our own search. Still the rule: never its
voice or its music; a frame with the source's caption, logo or watermark over the picture is cropped clean or left;
credited 元動画; told in our own words (YouTube penalises reused content: the more of the source a video shows, the
higher that risk, told to the owner). The shared note is in `maihaianh2911-bit/japan-video-factory` →
`docs/KENH-NHAT.md`; `tools/video_frames.py` of `japan-news-video-factory` lays out the shots of a video to choose
from (this repo has no such tool yet: cut the frames with ffmpeg and save them in `arc/<N>/own/`, the
`own/<file>` pictures of `AGENT_ARC.md`).

## Changing the pipeline
Before pushing to `main`: `python3 tests/arc_smoke.py --still`, `python3 -m compileall -q scripts tests`,
`npm run check`. Never touch secrets. Comments posted on GitHub start with 🤖 (they come from the owner's account).
No pull requests unless asked. The session cannot delete branches or tags.
