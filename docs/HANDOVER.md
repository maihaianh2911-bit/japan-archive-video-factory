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
- 13/11: bỏ lượt chạy Claude mỗi giờ (như repo văn học): Claude chỉ làm khi GitHub gọi, hoặc khi chủ kênh bấm **Gọi Claude ngay** / làm trong chat. Repo này dùng chung tác vụ Claude của `japan-video-factory`.
- 17/11 (phiếu 6–10): *"cho nhịp nhanh lên chút nhé"* → `"pace": "fast"` trong `script.json` (khoảng lặng giữa các câu ngắn lại), `fade` 0,35 giây, gần như mỗi câu một ảnh (~3 giây đổi ảnh); giọng đọc giữ tốc độ thường; video vẫn trên 60 giây.
- 16/11: **mỗi video phải kèm nội dung đăng bài** → Claude viết `arc/<N>/caption.txt` (tiếng Nhật: tiêu đề, 2–4 câu mô tả, 5–8 hashtag, dòng `画像出典`) ở bước chọn ảnh; máy đăng nó cạnh `video.mp4` trên nhánh `renders` và bình luận giao video có link caption cạnh video và phụ đề. Chỉ sửa `caption.txt` thì máy chỉ chép caption, không đọc lại giọng, không dựng lại. Đã viết bù cho phiếu 1–5.
- 16/11 — **LUẬT THÉP**: *"video ko đc dưới 60s, dưới 60s thì ko dựng"* → máy từ chối dựng video dưới 60 giây (`build.py`, kiểm tra trong `tests/arc_smoke.py`); bản xem trước cảnh báo; kịch bản viết 65–80 giây. Các video 2, 3, 5 (51–56 giây) được viết thêm câu và dựng lại.
- 16/11: *"nội dung gần gũi với người Nhật thay vì thế giới thì hay hơn"* → khi đề xuất chủ đề, ưu tiên lịch sử, truyền thuyết, phong tục của chính Nhật Bản mà người Nhật biết hoặc gặp hằng ngày (yêu quái, lễ hội, động đất, Edo, tranh ukiyo-e…), có tư liệu thật để minh họa.
- 14/11 (phiếu 1, tượng Dogū): *"dựng liền mạch ấy, đừng có chia ra từng cảnh"* → thêm `fade` trong `script.json` (ảnh sau hiện mờ dần trên ảnh trước thay vì cắt thẳng) và gom câu thành ít ý lớn (~10 s mỗi ý, tiêu đề giữ nguyên khi ảnh đổi). Mặc định vẫn cắt thẳng; dùng `fade` khi chủ kênh muốn liền mạch.
- 14/11: Claude phải **đọc từng câu rồi chọn cách edit hợp với ý câu đó** từ một bảng cách edit có tên, dựng trên bản mẫu đã duyệt → bảng 11 kiểu trong `AGENT_ARC.md` §2 (mã: `scripts/arc/edits.py`): `toan-canh`, `toan-canh-chi-tiet`, `khoanh`, `can-canh`, `tai-lieu-zoom`, `dung-yen`, `troi-cham`, `chan-dung`, `so-lieu`, `so-sanh`, `ket`. Mỗi ảnh trong `picks.json` ghi `"edit"` và `"why"`; máy xuất `edits.md` (cảnh số mấy, câu đọc, ảnh, kiểu edit, vì sao) và Claude dán bảng này vào bình luận giao video để chủ kênh chỉ cần viết "cảnh 5 đổi sang kiểu khoanh". Không thêm kiểu nào ngoài cách nhìn của bản mẫu; phiếu cũ không ghi `edit` vẫn dựng y như trước.
- 12/11: *"Tìm ảnh tự do, k cần ảnh wiki"* → máy tìm ở các kho ảnh mở (Openverse/Flickr, The Met, Art Institute of Chicago, Cleveland Museum of Art, Europeana, Thư viện Quốc hội Mỹ) và trang có giấy phép rõ ràng; Wikimedia không phải nguồn mặc định (chỉ dùng khi viết rõ `commons:`).

## Trạng thái (14/11/2026)

- 17/11 — **khâu tìm ảnh làm lại** (`scripts/find_images.py`), theo bản đã đo ở repo `germany-crime-video-factory`. **Đã vào `main` ngày 17/11** (chủ kênh: "đưa tất cả các phần đã cải thiện lên nhánh chính đi"); chưa chạy trên GitHub của repo này (mới thử trong phiên Claude): video đầu tiên sau ngày này là lần chạy thật đầu tiên, xem kỹ nhật ký bước tìm ảnh.
  - Vì sao: chủ kênh thấy video thiếu ảnh. Xem lại 10 phiếu đã làm: 195 từ khóa → 658 ảnh, 80 từ khóa không ra ảnh nào. Máy cũ chỉ lấy 8–12 ảnh đầu của mỗi kho, tải từng ảnh một. Thư viện Quốc hội Mỹ (`loc:`) rất chậm và hay từ chối máy GitHub: phiếu 4 mất 25 phút cho 2 từ khóa mà không được ảnh nào (máy thử lại 48 giây cho từng ảnh bị từ chối), phiếu 9 mất 8 phút cho 3 từ khóa (được 17 ảnh). Viện Nghệ thuật Chicago (`aic:`): 4 từ khóa, chưa lần nào ra ảnh (chưa rõ vì sao, chưa sửa).
  - Đã đổi: máy xem 20–30 ảnh của mỗi kho (Openverse tối đa 20), **chấm điểm từng ảnh so với lời mô tả** (mô hình mở CLIP, chạy ngay trên máy GitHub, không tốn tiền) và giữ 8 ảnh khớp nhất; từ khóa có thể kèm mô tả bằng tiếng Anh `{"q": …, "want": …}`, ảnh không khớp bị bỏ; tải vài ảnh cùng lúc, kho ảnh con chết chỉ mất tối đa 45 giây; kho nào báo "quá nhiều yêu cầu" (429) thì thôi hỏi đến hết lượt; ảnh Wikimedia lấy theo cỡ chuẩn (960, 1280, 1920, 3840 px), kể cả bản scan TIFF. Điểm hiện trên bảng ảnh (`~0.31`) và trong `index.json` (`match`). Không cài được CLIP thì máy tìm như cũ. Từ khóa viết kiểu cũ vẫn chạy.
  - Thư viện Quốc hội Mỹ **không còn nằm trong lượt tìm chung**, chỉ tìm khi viết rõ `loc:` (vẫn là kho ảnh mở như quyết định 12/11, chỉ đổi cách gọi).
  - Wikimedia: **giữ đúng quyết định 12/11** ("k cần ảnh wiki": không tìm mặc định, chỉ khi viết rõ). Thêm hai cách gọi cũng phải viết rõ: `wiki: <tên>` (mọi ảnh về một thứ: ảnh của bài Wikipedia tiếng Nhật và tiếng Anh, thư mục Commons, ảnh chụp tại chỗ; tới 24 ảnh) và `geo: <vĩ độ>,<kinh độ> <mét>`. Quy tắc "chỉ dùng khi không nơi nào khác có tư liệu" không đổi.
  - Bộ lọc ảnh không phù hợp (ảnh khỏa thân lẫn từ Flickr): ngưỡng đặt 0,24 thay vì 0,21 của repo Đức, vì chấm thử 658 ảnh cũ của kênh thì tượng đất Jōmon và netsuke kappa lên tới 0,23. Chưa thử với ảnh xấu thật.
  - Thử trong phiên (một lượt, 3 từ khóa, 2 phút 33 giây): `wiki: Hachikō` → 24 ảnh (đúng mục 忠犬ハチ公); `commons: 鯰絵` kèm mô tả "tranh khắc gỗ cá trê khổng lồ" → 8 tranh cá trê, điểm 0,25–0,37; `openverse: dogu` bị lỗi 401 vì xin 30 ảnh (Openverse chỉ cho 20) → đã sửa, chưa thử lại. Chấm lại 63 ảnh cũ của phiếu 1 theo mô tả "tượng đất Jōmon mắt to": 12 ảnh đứng đầu đều là tượng dogū.
  - `arc.yml` và `find-images.yml`: cài thêm bộ chấm điểm (torch, open_clip; lỗi cài thì bỏ qua) và giữ file mô hình 600 MB giữa các lượt chạy. Hướng dẫn viết từ khóa và chọn ảnh mới: `AGENT_ARC.md` §1 (`queries`) và §2 bước 2, 3, 5. Bài thử: `tests/find_units.py` (`tests/arc_smoke.py` tự chạy nó).
  - Trước khi đưa vào `main`: chạy một lượt tìm ảnh thật trên GitHub (workflow **Tìm ảnh**) để đo số ảnh và thời gian.
- Đã chạy thật trên GitHub: phiếu 1 (tượng Dogū, 19 câu, video 66 giây) xong trong 30 phút, làm trong chat. Thời gian đo được: giọng + kiểm tra giọng + tìm ảnh ~13 phút (17 từ khóa), dựng ~4–5 phút. Bài thử `tests/arc_smoke.py --still` chạy được.
- Secret `VN11_API_KEY` đã có. **`CLAUDE_TASK_URL` và `CLAUDE_TASK_TOKEN` chưa có trong repo này** (nhật ký ngày 14/11: mọi lần gọi Claude đều báo thiếu) → hiện chỉ có video khi làm trong chat; thêm hai khóa này (README "Cấu hình") thì mở phiếu là Claude tự làm.
- 14/11, sau đợt rà soát: gọi Claude thử lại 3 lần, không gọi được thì máy ghi ngay trên phiếu cách gọi lại (nút **Gọi Claude ngay**) và không còn viết "Claude sẽ…" khi chưa gọi được; câu đã đọc (đã trả tiền) được giữ ở `voice-cache/` khi bước giọng lỗi giữa chừng, lỗi máy nghe lại (Whisper) không làm mất giọng; không dựng bằng `picks.json` cũ trên ảnh vừa tìm lại; yêu cầu sửa viết trong lúc máy đang dựng không bị mất (giữ nhãn `arc-fix`); bình luận giao video nhắc link chỉ giữ đến khi phiếu ngừng hoạt động quá 14 ngày (máy dọn mỗi tuần — cách làm có từ đầu, ghi trong README; chủ kênh chưa nói gì khác).
- 13/11: đưa sang các sửa lỗi của repo văn học (12/11): giọng đọc được lưu lên nhánh `renders` ngay khi xong, trước khi tìm ảnh; nhãn thêm trước rồi mới bỏ, lỗi thì thử lại; đẩy lên `renders` thử lại từ bản mới nhất; máy dừng giữa chừng thì phiếu được đánh `arc-failed`; video trên 95 MB tự nén lại cho dưới giới hạn 100 MB của GitHub; đổi từ khóa ảnh đợt 1 khi đã có `picks.json` thì chờ Claude chọn lại; từ khóa tìm lỗi được ghi `"error"` trong `index.json`.
- Video mẫu: 720×1280; máy dựng 1080×1920 cùng tỉ lệ.

## Lưu ý kỹ thuật

- `gh` trong phiên cloud chỉ dùng REST (`gh api …`), lệnh GraphQL lỗi.
- Wikimedia chặn tải ảnh gốc kích thước tùy ý (lỗi 429): chỉ lấy các cỡ chuẩn (1920, 3840 px) — đã xử lý trong `scripts/find_images.py`.
- API tìm kiếm của The Met đổi sang `/public/collection/v1.1/search` từ 01/10/2026 (bản cũ trả 410).
- Europeana dùng khóa thử công khai `api2demo`; nếu bị giới hạn, đăng ký khóa miễn phí và đổi trong `scripts/find_images.py`.
- ffmpeg trên máy GitHub lấy từ gói pip `imageio-ffmpeg` (xem `scripts/arc/ff.py`). Ghim `faster-whisper==1.1.1` + `av==13.1.0`.
- Từ hay bị giọng đọc sai ghi vào `prompts/readings.json`.
