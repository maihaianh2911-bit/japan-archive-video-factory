# Cách edit từng cảnh

Muốn đổi thì viết, ví dụ: "cảnh 5 đổi sang kiểu khoanh" hoặc "cảnh 3 đứng yên thôi".

| Cảnh | Giây | Câu đọc | Ảnh | Kiểu edit | Vì sao |
|---|---|---|---|---|---|
| 1 | 0.0 | 口裂け女の口が裂けた理由にまつわる都市伝説。 | 映画『先生！口裂け女です！』（2023） | `troi-cham` — Trôi chậm | mở đầu: người đàn bà đeo khẩu trang, chưa lộ miệng |
| 2 | 3.6 | 多くの人は、整形手術に失敗したせいだと思っている。 | 昭和の手術風景（イメージ） | `troi-cham` — Trôi chậm | thuyết phẫu thuật thẩm mỹ hỏng |
| 3 | 7.4 | だが本当の理由は、「犬神の祟り」だ。 | 妖怪絵巻の「犬神」 | `troi-cham` — Trôi chậm | thẻ chữ 「犬神の祟り」 |
| 4 | 10.4 | 犬神とは、四国で恐れられてきた、犬の霊の憑きもの。 | 「犬神」（江戸時代の妖怪画） | `troi-cham` — Trôi chậm | 犬神 là gì |
| 5 | 13.9 | 飢えた犬の首をはね、その怨念を呪いに使ったのが始まりだ。 | 牙をむく犬（イメージ） | `troi-cham` — Trôi chậm | chặt đầu chó đói |
| 6 | 17.9 | 室町時代には、幕府が犬神使いを罰せよと命じたほどだ。 | 足利直義下知状（室町幕府の命令書） | `troi-cham` — Trôi chậm | Mạc phủ Muromachi ra lệnh |
| 7 | 22.0 | 口裂け女の一族は、先祖の悪行のせいで、 代々この犬神に呪われていた。 | 先祖の位牌（イメージ） | `troi-cham` — Trôi chậm | dòng họ, tổ tiên |
| 8 | 27.3 | そして彼女自身も、牙をむく犬のように、 口を耳まで裂かれてしまった。 | 映画『口裂け女』（2007） | `troi-cham` — Trôi chậm | miệng xé tới mang tai |
| 9 | 31.7 | 犬神に憑かれた者は、心を病み、犬のように吠え、犬のまねをする。 | 這い寄る女（イメージ） | `troi-cham` — Trôi chậm | bò như chó |
| 10 | 35.9 | 最初の噂の口裂け女が、 「精神科から逃げた女」だったのもそのためだ。 | 廃病院の廊下（イメージ） | `troi-cham` — Trôi chậm | trốn viện tâm thần |
| 11 | 40.5 | 目撃されるのがいつも女なのも、犬神が女に憑くからだ。 | 映画『口裂け女2』（2008） | `troi-cham` — Trôi chậm | luôn là phụ nữ |
| 12 | 44.3 | 漫画『地獄先生ぬ〜べ〜』でも、 口裂け女は犬神憑きの家の末裔として描かれた。 | 漫画『地獄先生ぬ〜べ〜』「恐怖の口裂け女の巻」 | `troi-cham` — Trôi chậm | truyện Nube |
| 13 | 49.7 | ポマードを嫌うのも、 犬神のせいで鼻が利きすぎるからだ。 | 昭和のポマード | `troi-cham` — Trôi chậm | sợ sáp vuốt tóc |
| 14 | 53.3 | 赤い服にマスクの女に「わたし、きれい？」 と聞かれたら、それは犬神に憑かれた口裂け女だ。 | 映画『口裂け女2』（2008） | `troi-cham` — Trôi chậm | thẻ chữ 「わたし、きれい？」, áo đỏ |
| 15 | 59.5 | 口は災いの元。答えを間違えれば、その牙で食い殺される。 | 映画『先生！口裂け女です！』（2023） | `troi-cham` — Trôi chậm | kết: bị cắn chết |

Lưu ý: ba cảnh liền nhau (đến cảnh 3) cùng một kiểu `troi-cham` — nên đổi một cảnh cho đỡ đều.

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
