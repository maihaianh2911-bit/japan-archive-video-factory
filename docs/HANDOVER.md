# Bàn giao dự án (đọc trước khi làm việc với chủ kênh)

Repo này làm **video lịch sử và truyền thuyết tiếng Nhật từ tư liệu thật** (Shorts dọc 1080×1920, 30 fps), dựng theo bản mẫu Göbekli Tepe đã duyệt (`00-video-mau/`). Được xây ngày 12/11/2026 theo cùng cách vận hành với repo văn học `maihaianh2911-bit/japan-video-factory` (phiếu → Claude chia ý → máy tạo giọng, tìm ảnh → Claude chọn ảnh, xem trước → máy dựng → Claude kiểm tra). Hai repo chạy độc lập.

## Chủ kênh

- GitHub `maihaianh2911-bit`. Nói chuyện **bằng tiếng Việt, ngắn gọn, dễ hiểu, không thuật ngữ**.
- Muốn **tự động hoàn toàn**: mở phiếu có kịch bản (tiếng Việt hoặc Nhật) là có video; góp ý thì sửa trên cùng phiếu.
- Chỉ dùng **hạn mức gói Claude** (dùng chung với các repo khác), không dùng Claude API trả tiền; không giảm chất lượng.

## Quy trình

Phiếu `[Lịch sử] …` → `.github/workflows/arc.yml` + `scripts/arc/run.py` (máy) và `AGENT_NIGHTLY.md` → `AGENT_ARC.md` (Claude):

`arc-plan` Claude viết `arc/<N>/script.json` (câu đọc, cảnh, tiêu đề, từ khóa tìm tư liệu) → `arc-voice` máy tạo giọng (11labs, một job mỗi câu), kiểm tra phát âm (Whisper), tìm ảnh ở các kho ảnh mở → `arc-pick` Claude xem ảnh, chọn, đặt khung / vòng khoanh / phóng, xem trước khung hình (`scripts/arc/preview.py`), viết `arc/<N>/picks.json` → `arc-render` máy dựng (`src/arc/ArcV.tsx`, Remotion) → `arc-check` Claude xem bảng cảnh → `arc-done`. Bình luận của chủ kênh → `arc-fix`. Kết quả: nhánh `renders`, thư mục `arc/<N>/`.

Bố cục đo từ bản mẫu (720×1280, phóng ×1,5): `scripts/arc/layout.py` dùng chung cho video và bản xem trước, nên bản xem trước đúng vị trí như video. Ví dụ đầy đủ (dựng lại bản mẫu bằng dữ liệu): `docs/vi-du-gobekli/`.

## Quyết định của chủ kênh (giữ nguyên khi làm)

- 12/11 (hướng dẫn `00-video-mau/HUONG-DAN-EDIT.md`): dùng ảnh thật, bản đồ gốc, bản scan, ảnh hiện vật, tranh cổ có nguồn; ghi rõ tranh minh họa và niên đại; **không** hình AI, ảnh tái dựng, cảnh "người nông dân đào ra di tích". Hình đi theo câu đọc; chỉ khoanh hoặc phóng khi có chi tiết cụ thể cần chỉ. Cắt thẳng ~3–5 s mỗi cảnh. Nhạc nhỏ hơn giọng. Diễn giải chưa xác nhận giữ ở mức giả thuyết. Thiếu ảnh phù hợp → tư liệu thật liên quan trực tiếp, hoặc sửa câu đọc cho khớp phần có thể minh họa.
- 12/11: mỗi cảnh lưu câu đọc, phụ đề, ảnh, trang nguồn, ghi công, khung cắt, mốc khoanh → `sources.json`; xuất MP4, SRT, danh sách nguồn.
- 12/11: *"Phần dựng hình, bố cục làm cho đẹp hơn đc ko, tao thấy đang hơi đơn điệu và màu đen ko bắt mắt lắm"* → thêm kiểu `warm` (nền là chính ảnh làm mờ, ảnh nổi có bóng và viền vàng, ảnh trôi chậm, vòng khoanh vẽ dần, tiêu đề hiện mượt, từ khóa phụ đề tô màu) và `paper` (nền giấy ngà); `classic` giữ đúng bản mẫu cũ. Bố cục (vị trí chữ, ảnh, phụ đề) giữ theo mẫu.
- 13/11: chủ kênh xem 2 video thử, chọn **Giấy cổ** (`paper`) làm mặc định.
- 12/11: *"Tìm ảnh tự do, k cần ảnh wiki"* → máy tìm ở các kho ảnh mở (Openverse/Flickr, The Met, Art Institute of Chicago, Cleveland Museum of Art, Europeana, Thư viện Quốc hội Mỹ) và trang có giấy phép rõ ràng; Wikimedia không phải nguồn mặc định (chỉ dùng khi viết rõ `commons:`).

## Trạng thái (12/11/2026)

- Mã đã viết và thử: bài thử `tests/arc_smoke.py --still` chạy được; dựng lại bản mẫu Göbekli Tepe bằng ảnh thật cho khung hình gần như trùng bản đã duyệt. Chưa chạy trên GitHub (cần secrets và tác vụ Claude hằng giờ, xem README "Cấu hình").
- Video mẫu: 720×1280; máy dựng 1080×1920 cùng tỉ lệ.

## Lưu ý kỹ thuật

- `gh` trong phiên cloud chỉ dùng REST (`gh api …`), lệnh GraphQL lỗi.
- Wikimedia chặn tải ảnh gốc kích thước tùy ý (lỗi 429): chỉ lấy các cỡ chuẩn (1920, 3840 px) — đã xử lý trong `scripts/find_images.py`.
- API tìm kiếm của The Met đổi sang `/public/collection/v1.1/search` từ 01/10/2026 (bản cũ trả 410).
- Europeana dùng khóa thử công khai `api2demo`; nếu bị giới hạn, đăng ký khóa miễn phí và đổi trong `scripts/find_images.py`.
- ffmpeg trên máy GitHub lấy từ gói pip `imageio-ffmpeg` (xem `scripts/arc/ff.py`). Ghim `faster-whisper==1.1.1` + `av==13.1.0`.
- Từ hay bị giọng đọc sai ghi vào `prompts/readings.json`.
