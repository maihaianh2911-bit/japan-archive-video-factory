# Cách edit từng cảnh

Muốn đổi thì viết, ví dụ: "cảnh 5 đổi sang kiểu khoanh" hoặc "cảnh 3 đứng yên thôi".

| Cảnh | Giây | Câu đọc | Ảnh | Kiểu edit | Vì sao |
|---|---|---|---|---|---|
| 1 | 0.0 | 青森県で見つかった、三千年前の不思議な土の人形。 大きな目は、まるでゴーグルをかけているようです。 | 遮光器土偶（亀ヶ岡遺跡出土） | `tai-lieu-zoom` — Tài liệu rồi phóng vào | câu 1 giới thiệu cả bức tượng, câu 2 nói về đôi mắt: cho thấy cả tượng rồi phóng vào mắt |
| 2 | 7.2 | これは「遮光器土偶」。 縄文時代の終わりごろに作られました。 | 遮光器土偶（縄文時代晩期） | `can-canh` — Cận cảnh có chú thích | câu gọi tên tượng: nhìn sát khuôn mặt, có chữ ghi cách đọc tên |
| 3 | 11.8 | 一番有名なものは、明治時代に亀ヶ岡遺跡で見つかりました。 | 亀ヶ岡遺跡（青森県つがる市） | `toan-canh` — Toàn cảnh | câu nhắc nơi tìm thấy: cho thấy di chỉ Kamegaoka |
| 4 | 16.2 | 高さは三十四センチほど。中は空洞になっています。 | 遮光器土偶（後ろ姿） | `so-lieu` — Con số / mốc thời gian | câu có con số chiều cao: tiêu đề đổi thành con số |
| 5 | 19.9 | 今は東京国立博物館に収められています。 | 東京国立博物館 本館 | `toan-canh` — Toàn cảnh | câu nhắc bảo tàng đang giữ tượng |
| 6 | 23.4 | 「遮光器」とは、北極の人々が使う雪よけの眼鏡のこと。 | イヌイットの雪よけ眼鏡 | `dung-yen` — Đứng yên | chiếc kính tuyết thật: để yên cho người xem nhìn khe hẹp |
| 7 | 27.4 | 目の形がその眼鏡に似ていたので、この名前がつきました。 | 雪よけ眼鏡と土偶の目 | `so-sanh` — So sánh hai ảnh | câu nói mắt tượng giống chiếc kính: đặt hai thứ cạnh nhau |
| 8 | 31.1 | やがて、「宇宙服を着た宇宙人だ」という説まで広まりました。 丸くふくらんだ体や肩が、宇宙服に見えたのです。 | 遮光器土偶（ロサンゼルス郡立美術館） | `troi-cham` — Trôi chậm | lời đồn người ngoài hành tinh: tấm ảnh nền tối, vai phồng như áo vũ trụ, cho trôi chậm để ngắm |
| 9 | 38.1 | しかし研究者の多くは、 閉じた目を大きく表したものだと考えています。 | 亀ヶ岡遺跡出土の土偶（辰馬考古資料館） | `khoanh` — Khoanh chi tiết | câu nói mắt là mắt nhắm: khoanh đôi mắt có một đường kẻ ngang |
| 10 | 42.9 | 胸やお腹のふくらみから、女性の姿だという見方もあります。 | 遮光器土偶（縄文時代晩期） | `can-canh` — Cận cảnh có chú thích | câu nhắc ngực và bụng: cắt sát vào thân tượng |
| 11 | 46.7 | そして不思議なことに、この土偶は左足が欠けています。 | 遮光器土偶（東京国立博物館） | `khoanh` — Khoanh chi tiết | câu nói tượng mất chân trái: khoanh đúng chỗ chân bị mất khi giọng đọc nhắc |
| 12 | 50.6 | 土偶の多くは、こうして壊れた姿で見つかります。 | 伊勢堂岱縄文館の土偶（秋田県） | `toan-canh` — Toàn cảnh | câu nói nhiều tượng được tìm thấy khi đã vỡ: một tủ trưng bày toàn tượng vỡ |
| 13 | 53.8 | 病気やけがの身代わりに、 わざと壊したのではないか、という説もあります。 | 土偶のかけら（縄文時代） | `dung-yen` — Đứng yên | giả thuyết cố ý đập vỡ: các mảnh vỡ, để yên cho người xem nhìn |
| 14 | 58.3 | けれど、本当の答えは、まだわかっていません。 三千年前の人々は、この目で何を見ていたのでしょうか。 | 遮光器土偶（亀ヶ岡遺跡出土） | `ket` — Câu hỏi kết | câu hỏi kết về đôi mắt: quay lại đôi mắt của bức tượng nổi tiếng nhất |

## Các kiểu edit có thể chọn

| Kiểu | Trông thế nào | Dùng khi |
|---|---|---|
| `toan-canh` — Toàn cảnh | cả tấm ảnh, rộng hết khung, trôi vào rất chậm | câu nhắc một địa điểm, di tích, tòa nhà: cho thấy toàn bộ nơi đó |
| `toan-canh-chi-tiet` — Toàn cảnh + ô chi tiết | ảnh rộng ở trên, một ô phóng một phần của chính ảnh đó ở dưới | câu nói "ở đâu" rồi "có gì ở đó": ảnh toàn cảnh rất ngang, cần thấy rõ thêm một chỗ |
| `so-sanh` — So sánh hai ảnh | hai ảnh khác nhau xếp trên dưới, đứng yên | câu so sánh hai vật ("giống như…", "khác với…", trước và sau) |
| `khoanh` — Khoanh chi tiết | ảnh đứng yên, vòng khoanh hiện đúng lúc giọng đọc nhắc tới vật đó | câu chỉ vào một cấu trúc hay vị trí trong ảnh (vòng cột đá, một căn phòng trên sơ đồ, một dấu trên bản đồ) |
| `can-canh` — Cận cảnh có chú thích | cắt sát vào chi tiết, dòng chú thích vàng nhỏ dưới ảnh | câu nhắc một hình chạm khắc, dòng chữ, bộ phận của hiện vật: phải nhận ra được vật đó |
| `tai-lieu-zoom` — Tài liệu rồi phóng vào | cả tài liệu trước, rồi phóng chậm vào đúng phần được nhắc | bản đồ, bản thảo, phiến đất sét, trang sách: người xem thấy nó là gì rồi mới thấy chỗ được nói tới |
| `dung-yen` — Đứng yên | cả tấm ảnh, không chuyển động | bản đồ, trang chữ, sơ đồ cần thời gian đọc; cũng dùng để nghỉ giữa hai cảnh có chuyển động |
| `troi-cham` — Trôi chậm | cả tấm ảnh, trôi vào rõ hơn một chút | truyền thuyết, thần thoại, cảnh trong tranh cổ, bản khắc: để người xem ngắm bức tranh |
| `chan-dung` — Chân dung | ảnh hoặc tranh người, giữ nguyên cả hình, chú thích tên và năm dưới ảnh | câu nhắc một người có thật (nhà khảo cổ, vua, tác giả): chân dung thật của người đó |
| `so-lieu` — Con số / mốc thời gian | tiêu đề lớn đổi thành con số hay năm, ảnh đứng yên | câu có con số, niên đại, kích thước, hoặc nhảy sang một thời khác ("năm 1887…", "ba nghìn năm trước…") |
| `ket` — Câu hỏi kết | tấm ảnh ấn tượng nhất của chủ đề, trôi vào chậm đến hết video | câu hỏi hoặc điều bí ẩn ở cuối video |
