# japan-archive-video-factory

Dây chuyền làm **video lịch sử và truyền thuyết tiếng Nhật** khổ dọc 9:16 (1080×1920) cho Shorts, bằng **tư liệu thật**: ảnh khai quật, ảnh hiện vật, bản đồ gốc, bản scan, tranh khắc và tranh cổ có nguồn (không dùng ảnh AI hay ảnh tái dựng). Giọng đọc và phụ đề tiếng Nhật. Chạy hoàn toàn trên GitHub.

Bố cục theo bản mẫu đã duyệt **Göbekli Tepe**: [`00-video-mau/MAU-EDIT-20S.mp4`](00-video-mau/MAU-EDIT-20S.mp4), hướng dẫn [`00-video-mau/HUONG-DAN-EDIT.md`](00-video-mau/HUONG-DAN-EDIT.md). Chữ vàng nhỏ ở trên (địa điểm / loại tư liệu), tiêu đề Nhật màu kem, ảnh ở giữa có viền mảnh, phụ đề dưới ảnh, ghi công ở chân khung. Hình đổi theo câu đọc: toàn cảnh khi nói về địa điểm, ảnh từ trên cao và **khoanh vòng** đúng lúc nói về bố cục, ảnh cận khi nói về phù điêu, **phóng** vào đúng chỗ trên bản đồ. Cắt thẳng, nhạc nền nhỏ hơn giọng.

Kiểu hình (ghi trong Ghi chú của phiếu nếu muốn đổi): **Giấy cổ** (mặc định — nền giấy ngà, chữ nâu mực, ảnh như tấm ảnh in có viền trắng, ảnh trôi chậm, vòng khoanh đỏ vẽ dần), **Ấm** (nền là chính bức ảnh làm mờ nên mỗi cảnh có màu riêng), **Cổ điển** (nền nâu đen phẳng như bản mẫu đầu tiên).

## Làm một video

1. **Issues → New issue → 🏛️ Video lịch sử / truyền thuyết** ([mở thẳng](https://github.com/maihaianh2911-bit/japan-archive-video-factory/issues/new/choose)). Dán kịch bản (tiếng Việt hoặc tiếng Nhật) → **Create**. ChatGPT cũng tạo phiếu được, theo mẫu trong [`docs/CHATGPT.md`](docs/CHATGPT.md).
2. Không cần làm gì thêm. Claude chia lời theo cảnh (dịch sang tiếng Nhật nếu cần) → máy tạo giọng đọc, tự kiểm tra phát âm, tìm tư liệu ở các kho ảnh mở → Claude xem từng ảnh, chọn ảnh đúng với câu đọc, đặt vòng khoanh / khung phóng, xem trước khung hình → máy dựng video → Claude kiểm tra lại từng cảnh. Mỗi bước báo trong phiếu.
3. Bình luận cuối có link **xem / tải video (MP4)**, **phụ đề** (SRT), **nguồn ảnh** (dán vào mô tả video) và **bảng nguồn từng cảnh**.
4. Muốn sửa: viết **một bình luận** gom hết yêu cầu, ví dụ "cảnh 3 khoanh vòng đá bên trái, câu 5 đọc sai tên". Claude sửa và dựng lại trên cùng phiếu.

## Nguồn tư liệu

Máy tìm ở các kho ảnh mở, chỉ lấy ảnh được phép dùng trong video kiếm tiền (phạm vi công cộng, CC0, CC BY, CC BY-SA): **Openverse** (Flickr và các bộ sưu tập CC), **The Met**, **Art Institute of Chicago**, **Cleveland Museum of Art**, **Europeana** (thư viện, bảo tàng châu Âu), **Thư viện Quốc hội Mỹ**. Claude cũng có thể thêm ảnh từ trang có giấy phép rõ ràng (ví dụ hình trong bài báo khoa học CC BY, như ảnh trên cao trong bản mẫu). Wikimedia chỉ dùng khi không nơi nào khác có tư liệu đó.

## Nhãn trên phiếu (máy tự gắn)

| Nhãn | Ý nghĩa |
|---|---|
| `arc-plan` | Chờ Claude chia cảnh và chọn từ khóa tìm tư liệu |
| `arc-voice` | Máy đang tạo giọng đọc và tìm tư liệu |
| `arc-pick` | Chờ Claude chọn ảnh |
| `arc-render` | Máy đang dựng video |
| `arc-check` | Chờ Claude kiểm tra từng cảnh |
| `arc-done` | Video xong (link ở bình luận cuối) |
| `arc-fix` | Bạn yêu cầu sửa, Claude sẽ làm |
| `arc-failed` | Máy gặp lỗi, Claude sẽ xem |
| `arc-busy` | Claude đang làm phiếu này (trong chat hoặc tác vụ tự động), tác vụ khác không làm chồng lên |

## File kết quả

Nhánh **`renders`**, thư mục `arc/<số phiếu>/`: `video.mp4`, `subtitles.srt`, `credits.txt` (nguồn ảnh), `sources.json` (từng cảnh: câu đọc, ảnh, trang nguồn, ghi công, khung cắt, mốc khoanh), `sheet.jpg` (ảnh các cảnh). Video của phiếu không hoạt động quá 14 ngày sẽ được dọn tự động, nên hãy tải về sớm.

## Cấu hình (làm một lần)

- **Secrets** (Settings → Secrets and variables → Actions): `VN11_API_KEY` (giọng đọc 11labs, giống repo văn học), `CLAUDE_TASK_URL` + `CLAUDE_TASK_TOKEN` (để GitHub gọi Claude khi có việc; dùng **cùng giá trị** như repo văn học `japan-video-factory` khi dùng tác vụ chung). Không có lượt chạy mỗi giờ: thiếu hai secret này thì phiếu chờ đến khi làm trong chat.
- Tác vụ Claude: tác vụ chung của các kênh (tác vụ của `japan-video-factory`) làm luôn phiếu lịch sử; nếu mỗi repo có tác vụ Claude riêng thì tác vụ của repo này làm (lời nhắn: "Làm theo AGENT_NIGHTLY.md của repo maihaianh2911-bit/japan-archive-video-factory."). Cả hai đều đọc [`AGENT_NIGHTLY.md`](AGENT_NIGHTLY.md).
- Giọng: `clone_190` (kể chuyện, mặc định) hoặc `clone_461` (tin tức), chọn trong phiếu.

## Chạy tay (tab **Actions**)

| Workflow | Làm gì |
|---|---|
| **Video lịch sử (tư liệu thật)** | Chạy lại một bước cho một phiếu: `prepare` (giọng + ảnh), `search` (tìm thêm ảnh), `render` (dựng) |
| **Gọi Claude ngay** | Gọi Claude làm tiếp khi phiếu đang chờ (ví dụ sau khi hết hạn mức) |
| **Tìm ảnh (kho ảnh mở)** | Tìm ảnh miễn bản quyền theo từ khóa |
| **Dọn video cũ (nhánh renders)** | Dọn file của phiếu cũ (tự chạy mỗi tuần) |

Hướng dẫn cho Claude: [`AGENT_NIGHTLY.md`](AGENT_NIGHTLY.md) (điểm vào khi GitHub gọi Claude) và [`AGENT_ARC.md`](AGENT_ARC.md) (các bước làm video). Bàn giao và các quyết định của chủ kênh: [`docs/HANDOVER.md`](docs/HANDOVER.md).
