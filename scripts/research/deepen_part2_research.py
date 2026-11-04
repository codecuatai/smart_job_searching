"""Research-backed revision of Part 2 in the consolidated UniTalent proposal."""

from pathlib import Path
from copy import deepcopy
import sys

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "docs" / "research" / "De_Xuat_UniTalent_AI_Tong_Hop.docx"
OUTPUT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else PATH
doc = Document(PATH)
body = doc.element.body
items = list(doc.iter_inner_content())
start = next(x for x in items if x.__class__.__name__ == "Paragraph" and x.text.startswith("PHẦN 2:"))
end = next(x for x in items if x.__class__.__name__ == "Paragraph" and x.text.startswith("PHẦN 3:"))

node = start._p.getnext()
while node is not end._p:
    next_node = node.getnext()
    body.remove(node)
    node = next_node

start.text = "PHẦN 2: CHIẾN LƯỢC NGUỒN DỮ LIỆU ĐẦU VÀO VÀ QUYỀN KHAI THÁC"
start.runs[0].bold = True
start.runs[0].font.size = Pt(14)
start.runs[0].font.color.rgb = RGBColor(20, 45, 85)

added = []


def para(text, *, heading=False, small=False, bullet=False):
    p = doc.add_paragraph(style="List Bullet" if bullet else "Normal")
    r = p.add_run(text)
    if heading:
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(30, 115, 190)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
    elif small:
        r.font.size = Pt(8.5)
        p.paragraph_format.space_after = Pt(2)
    else:
        p.paragraph_format.space_after = Pt(5)
        if text.startswith(("Tất cả bản ghi", "Ngưỡng nghiệm thu", "Kết luận chọn nguồn")):
            p.paragraph_format.space_before = Pt(6)
        if text.startswith(("Ngưỡng nghiệm thu", "Tất cả bản ghi")):
            p.paragraph_format.keep_together = True
    added.append(p._p)
    return p


def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, (h, w) in enumerate(zip(headers, widths)):
        t.columns[i].width = Inches(w)
        c = t.rows[0].cells[i]
        c.width = Inches(w)
        c.text = h
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        tcpr = c._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "1E73BE")
        tcpr.append(shd)
        for p in c.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
    trpr = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    trpr.append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for i, (value, w) in enumerate(zip(row, widths)):
            cells[i].width = Inches(w)
            cells[i].text = value
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(8.4)
                    r.font.color.rgb = RGBColor(33, 37, 41)
    for row in t.rows:
        trpr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        trpr.append(cant_split)
        for c in row.cells:
            tcpr = c._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for side in ("top", "left", "bottom", "right"):
                x = OxmlElement(f"w:{side}")
                x.set(qn("w:w"), "90")
                x.set(qn("w:type"), "dxa")
                mar.append(x)
            tcpr.append(mar)
    added.append(t._tbl)
    return t


para("Chiến lược khả thi bắt đầu từ ba nguồn có quyền kiểm soát trực tiếp: tin tuyển dụng do doanh nghiệp đăng hoặc cấp qua ATS, hồ sơ ứng viên tự cung cấp và sự kiện phát sinh trong UniTalent AI. Nguồn bên ngoài chỉ được nạp khi có căn cứ sử dụng rõ ràng. Mỗi nguồn được đánh giá theo quyền khai thác, độ bao phủ, độ mới, khả năng xác minh và chi phí duy trì; không mặc định dữ liệu nhìn thấy công khai là dữ liệu được phép sao chép, tái phân phối hoặc dùng huấn luyện mô hình.")

para("2.1. Ma trận nguồn dữ liệu và thứ tự triển khai", heading=True)
para("P0 là đầu vào cho bản thử nghiệm; P1 làm giàu bằng chứng năng lực và ngữ nghĩa; P2 chỉ mở khi đạt điều kiện pháp lý và kỹ thuật. Tần suất bên dưới là đề xuất thiết kế, không phải quyền API hoặc cam kết từ nền tảng.")
table(
    ["Nguồn / mức ưu tiên", "Dữ liệu nhận", "Kênh và nhịp nạp đề xuất", "Điều kiện sử dụng / đầu ra"],
    [
        ("Doanh nghiệp đăng JD trực tiếp — P0", "JD, điều kiện làm việc, trạng thái tuyển, hồ sơ tổ chức", "Biểu mẫu và API nội bộ; theo sự kiện đăng, sửa, đóng tin", "Điều khoản với doanh nghiệp; xác minh người đăng; nguồn việc chính của MVP"),
        ("ATS / doanh nghiệp đối tác — P0", "Job ID đối tác, JD, cập nhật, hết hạn", "Webhook hoặc feed JSON/XML/CSV; đối soát định kỳ theo hợp đồng", "Thỏa thuận cho nhận, lưu và hiển thị; quy định xóa, ghi công, chuyển hướng"),
        ("Ứng viên tự nhập / tải CV — P0", "Kỹ năng, học vấn, dự án, nguyện vọng, CV gốc và trường trích xuất", "Upload PDF/DOCX, biểu mẫu, sự kiện sửa hồ sơ", "Thông báo mục đích và quyền chọn chia sẻ; ứng viên xác nhận trường AI bóc tách"),
        ("Sự kiện ứng dụng — P0", "Xem, lưu, ứng tuyển, trạng thái xử lý, phản hồi", "Event có schema; ghi khi phát sinh; tổng hợp theo kỳ", "Giảm định danh, giới hạn mục đích và thời hạn; không chứa CV hoặc thông tin liên hệ"),
        ("GitHub do ứng viên chọn — P1", "Repository được chọn, README, ngôn ngữ, metadata commit, bằng chứng dự án", "GitHub App quyền đọc tối thiểu; nạp khi ứng viên yêu cầu hoặc repo đổi", "Ứng viên chọn repo và có thể ngắt kết nối; không đánh đồng số commit với năng lực"),
        ("ESCO / O*NET — P1", "Mã nghề, nhãn kỹ năng, đồng nghĩa, quan hệ nghề–kỹ năng", "Tải bản công bố hoặc API; cập nhật theo phiên bản phát hành", "Ghi phiên bản, giấy phép, nguồn và cách chuyển đổi; bổ sung từ điển nghề Việt Nam"),
        ("Trang tuyển dụng / job board bên ngoài — P2", "JD được cấp quyền, URL gốc, trạng thái tuyển", "API/feed theo thỏa thuận; HTML có phép khi không có feed", "Chỉ nạp sau khi xác nhận phạm vi sử dụng, tần suất, giữ bản sao và cách thu hồi"),
    ],
    [1.18, 1.65, 1.67, 2.00],
)

para("2.2. Nguồn tin tuyển dụng: ai sở hữu dữ liệu, hệ thống nhận bằng cách nào", heading=True)
para("2.2.1. Tin do doanh nghiệp tạo và ATS đối tác cấp. Biểu mẫu đăng tin là nguồn có khả năng kiểm soát cao nhất: nhà tuyển dụng nhập chức danh, mô tả, địa điểm/remote, hình thức, cấp bậc, điều kiện bắt buộc/ưu tiên, hạn ứng tuyển và trạng thái. Hệ thống kiểm tra tài khoản tổ chức, yêu cầu người đăng xác nhận quyền đại diện, gắn employer_id và version. Với ATS, khóa ngoài gồm partner_id + external_job_id; webhook nhận create/update/close và tác vụ đối soát phát hiện webhook bị mất. Hợp đồng phải nói rõ UniTalent được lưu nội dung nào, hiển thị trong bao lâu, có được tạo embedding hay báo cáo tổng hợp hay không, và phải làm gì khi đối tác đóng hoặc rút tin.")
para("2.2.2. LinkedIn và Indeed không được coi là nguồn lấy toàn bộ việc làm mặc định. Tài liệu chính thức của LinkedIn mô tả Job Posting API cho đối tác ATS đưa tin lên LinkedIn và quản lý vòng đời tin; Indeed Job Sync API cũng cho đối tác ATS tạo, cập nhật và hết hạn tin trên Indeed [S1][S2]. Đây là chiều dữ liệu từ UniTalent/ATS sang nền tảng, không chứng minh có API công khai để UniTalent lấy hàng loạt JD từ họ. Vì vậy tích hợp hai nền tảng chỉ là phương án xuất bản tin của doanh nghiệp sau khi trở thành đối tác được phê duyệt; nguồn JD đi vào hệ thống phải có feed/quyền nhận riêng được ghi trong thỏa thuận. Khi chưa có, hệ thống chỉ liên kết đến tin gốc nếu cách hiển thị và điều khoản của nguồn cho phép.")
para("2.2.3. Website tuyển dụng nội địa (ví dụ TopCV, VietnamWorks, ITviec) là danh sách đối tác tiềm năng, không phải quyền crawl đã có. Ưu tiên API, feed hoặc file do chính đơn vị vận hành cung cấp. Nếu nhận HTML theo thỏa thuận, đọc dữ liệu JobPosting có cấu trúc khi trang cung cấp rồi dùng parser có phiên bản; dữ liệu cấu trúc giúp xác định title, description, hiringOrganization, jobLocation, datePosted, validThrough nhưng bản thân markup không cấp phép sao chép nội dung [S3]. Chỉ lấy các trường được cho phép; lưu URL chuẩn, thời điểm lấy và điều kiện sử dụng; dừng và gỡ bản ghi khi hợp đồng hết hiệu lực hoặc nguồn yêu cầu. Không vượt đăng nhập, CAPTCHA hay biện pháp chặn để lấy dữ liệu.")
para("2.2.4. So sánh các nền tảng tuyển dụng được nêu trong đề bài", heading=True)
para("Bảng dưới đây phân biệt giá trị dữ liệu với quyền thực sự được xác minh. 'Chưa xác minh' nghĩa là nghiên cứu tài liệu công khai trong phạm vi đề xuất này chưa xác nhận được API hoặc giấy phép đưa tin vào UniTalent; đây không phải kết luận nền tảng không có chương trình đối tác.")
table(
    ["Nguồn", "Dữ liệu có ích cho hệ thống", "API và quyền sử dụng đã kiểm chứng", "Quyết định cho UniTalent"],
    [
        ("LinkedIn", "JD, chức danh, kỹ năng và thông tin tổ chức nếu có quyền nhận.", "Job Posting API công bố là kênh ATS đăng/quản lý tin lên LinkedIn; quyền API Talent cần phê duyệt. Chưa xác minh kênh công khai lấy kho JD về [S1][S9].", "Không dùng làm nguồn nạp mặc định. Chỉ xét xuất bản JD sau khi được chấp thuận đối tác."),
        ("Indeed", "JD, yêu cầu, lương và địa điểm nếu có feed được cấp.", "Job Sync API cho ATS tạo/cập nhật/hết hạn tin trên Indeed; danh mục API công bố không xác nhận feed tìm kiếm toàn bộ JD cho bên thứ ba [S2][S10].", "Không tính vào độ phủ đầu vào MVP. Chỉ tích hợp theo chương trình đối tác và mục đích được cấp."),
        ("TopCV", "Tin tuyển dụng và tín hiệu thị trường việc làm Việt Nam.", "Điều khoản TopCV nêu việc thu thập dữ liệu bằng công cụ bên thứ ba cần sự đồng ý; không suy ra quyền từ tin hiển thị công khai [S11].", "Chỉ nhận API/feed hoặc nội dung theo thỏa thuận rõ phạm vi lưu, hiển thị và thời hạn."),
        ("VietnamWorks", "Tin tuyển dụng tổng hợp tại Việt Nam.", "Chưa xác minh được API nạp tin hoặc giấy phép tái sử dụng từ tài liệu chính thức trong lần rà soát này.", "Đưa vào danh sách liên hệ đối tác; chưa đưa dữ liệu vào pipeline hay cam kết độ phủ."),
        ("ITviec", "JD công nghệ và mô tả kỹ năng chuyên ngành.", "Quy chế ITviec giới hạn sao chép/phân phối nội dung, công cụ tương tự khi chưa có sự đồng ý [S12]. Chưa xác minh feed nhận JD công khai.", "Ưu tiên đề nghị feed có phép; không crawl và đăng lại khi chưa có thỏa thuận."),
        ("Doanh nghiệp / ATS ký kết", "JD gốc, thay đổi, đóng tin, điều kiện bắt buộc và thông tin xác minh tổ chức.", "Quyền nhận dữ liệu được xác lập trực tiếp trong điều khoản/hợp đồng của UniTalent với từng đơn vị.", "Nguồn P0 cho MVP; đối soát trạng thái và trách nhiệm gỡ tin."),
    ],
    [1.06, 1.17, 2.39, 1.88],
)
para("Kết luận chọn nguồn: MVP không phụ thuộc vào việc được cấp API LinkedIn, Indeed hoặc quyền sao chép từ các job board. Chỉ tiêu độ phủ của MVP chỉ tính tin do doanh nghiệp nhập và feed đối tác đã có hợp đồng. Mỗi nguồn P2 phải có tài liệu nêu rõ chiều dữ liệu, trường được nhận, tần suất, quyền lưu/hiển thị/tạo embedding, cách ghi nguồn và quy trình gỡ tin trước khi đưa vào kế hoạch triển khai.")

para("2.3. Nguồn hồ sơ, bằng chứng kỹ năng và từ điển chuẩn", heading=True)
para("2.3.1. CV và hồ sơ ứng viên. Người dùng tự tải PDF/DOCX hoặc điền hồ sơ. Pipeline bóc tách văn bản trước, OCR chỉ khi tài liệu là ảnh; nhận dạng tên trường, không tự coi kết quả OCR/NER là sự thật. Mỗi giá trị kỹ năng, trường học, dự án, chứng chỉ có origin (tự khai, CV, nhà tuyển dụng xác nhận), confidence, extracted_at và trạng thái user_confirmed. Ứng viên có màn hình sửa trước khi hồ sơ đi vào so khớp. Tệp CV gốc được tách khỏi chỉ mục tìm kiếm và chỉ người có quyền mới đọc; thông tin liên hệ không đưa vào embedding hoặc log. Thiếu GPA, lương kỳ vọng hay năm kinh nghiệm không được diễn giải thành năng lực thấp.")
para("2.3.2. GitHub là bằng chứng dự án tự nguyện, không phải phép đo trực tiếp chất lượng lập trình. GitHub khuyến nghị GitHub App chỉ xin quyền tối thiểu; ứng viên chọn repository được chia sẻ [S4]. Ở giai đoạn P1, hệ thống đọc metadata, README, ngôn ngữ và một số tệp do người dùng cho phép; hạn chế kích thước, bỏ secrets, dữ liệu cá nhân và file sinh tự động. Kết quả phân tích nên thể hiện “repo có dấu hiệu sử dụng Java/Spring” kèm đường dẫn, commit SHA và độ tin cậy; không tự kết luận tác giả duy nhất, Clean Code, đạo văn hay năng lực thuật toán chỉ từ số commit. Ngắt kết nối phải ngừng đồng bộ và kích hoạt chính sách xóa bản sao/đặc trưng đã trích.")
para("2.3.3. ESCO và O*NET dùng để chuẩn hóa, không thay thế ngữ cảnh tuyển dụng Việt Nam. ESCO có bộ tải miễn phí ở nhiều định dạng; O*NET phát hành cơ sở dữ liệu nghề, kỹ năng và API [S5][S6]. Mỗi khái niệm lưu taxonomy_name, concept_id/URI, label, ngôn ngữ, phiên bản, từ đồng nghĩa, ngày nạp và giấy phép. Từ khóa “React”, “ReactJS” chỉ nối vào khái niệm chuẩn khi thực sự có mã phù hợp; nếu không, giữ alias nội bộ có người kiểm duyệt. Cần bảng ánh xạ chức danh Việt–Anh và vai trò Fresher/Intern; quan hệ nghề của O*NET phản ánh thị trường Mỹ nên chỉ là tham khảo khi chấm điểm việc làm tại Việt Nam.")

para("2.4. Từ điển trường tối thiểu và chứng cứ nguồn", heading=True)
table(
    ["Thực thể", "Trường bắt buộc để dùng", "Trường có thể thiếu", "Kiểm tra / truy vết"],
    [
        ("JD", "source_id, external_job_id hoặc job_id, employer_id, title, description, work_location hoặc remote_type, employment_type, status, source_url (nếu có), fetched_at", "salary_min/max, currency, salary_period, posted_at, expires_at, benefits, preferred_skills", "Giữ raw version, quyền sử dụng, thời điểm hiệu lực; không suy diễn lương trống thành 0; đóng tin khi nguồn hết hạn"),
        ("Ứng viên", "candidate_id, consent_version, kỹ năng/học vấn do người dùng xác nhận, updated_at", "GPA, năm kinh nghiệm, chứng chỉ, GitHub, lương mong muốn", "Tách PII; lưu source và confidence cho từng trường; thay đổi của người dùng ưu tiên hơn OCR"),
        ("Sự kiện", "event_id, pseudonymous_user_id, event_type, job_id, occurred_at, purpose_version", "experiment_id, device category, vị trí trong danh sách", "Khử trùng event_id; không có email/số điện thoại/CV; lọc bot và ghi rõ thời điểm thực"),
        ("Taxonomy", "source, concept_id/URI, label, language, version", "alias, related_skill, occupation mapping", "Lưu giấy phép và phép ánh xạ; trường chưa xác minh giữ mã nội bộ"),
    ],
    [0.82, 2.30, 1.56, 1.82],
)
para("Tất cả bản ghi bên ngoài có thêm acquisition_method, agreement_id/license_scope, retention_rule, source_last_seen_at, parser_version và quality_status. Các trường này cho phép trả lời một tin đến từ đâu, được phép hiển thị hay tạo embedding không, được sửa lúc nào và phải gỡ khi nào. Sổ đăng ký nguồn (source registry) đặt điều kiện quyền và thời hạn trước khi pipeline nạp dữ liệu; không có agreement_id phù hợp thì dữ liệu vào hàng chờ, không vào chỉ mục công khai.")

para("2.5. Kiểm soát chất lượng theo nguồn và rủi ro sử dụng", heading=True)
table(
    ["Rủi ro", "Dấu hiệu / phép đo", "Cách xử lý đề xuất"],
    [
        ("Tin hết hạn, thay đổi hoặc trùng", "URL/ID lặp, status đóng, expires_at cũ, nguồn mất tin", "Đối soát trạng thái; gộp theo ID và fingerprint; giữ lịch sử phiên bản, gỡ khỏi kết quả khi đóng"),
        ("JD thiếu trường hoặc sai lương", "Thiếu title/mô tả/địa điểm; min > max; kỳ lương mơ hồ", "Chặn trường bắt buộc; yêu cầu doanh nghiệp sửa; lương không rõ giữ trống, ước tính hiển thị riêng"),
        ("CV trích xuất sai hoặc thiên lệch", "Confidence thấp, hai nguồn mâu thuẫn, ký tự OCR lỗi", "Ứng viên xác nhận; đánh giá trên bộ CV nhiều bố cục/ngôn ngữ; không lọc ứng viên vì trường chưa xác minh"),
        ("Giả mạo tin và tổ chức", "Tên miền/email không khớp, yêu cầu ứng viên chuyển tiền, JD bất thường", "Xác minh tổ chức và duyệt thủ công trường hợp rủi ro; lưu lý do và kênh khiếu nại"),
        ("Tương tác bị lệch mẫu", "Chỉ quan sát người đã được hiển thị; click do thứ hạng và quảng cáo", "Tách impression/click/apply; đánh giá theo vị trí, nguồn, nhóm; không coi click là bằng chứng năng lực"),
        ("Quyền và bảo mật", "Nguồn hết phép, consent rút, token lộ, dữ liệu tồn sau yêu cầu xóa", "Chặn theo policy trước nạp và trước xuất; token trong secret store; xóa/ẩn bản gốc, chỉ mục, vector, bản sao theo lịch"),
    ],
    [1.35, 2.25, 2.90],
)
para("Ngưỡng nghiệm thu cần đo trong pilot và ghi rõ mẫu số: tỷ lệ JD đủ trường tối thiểu; tỷ lệ tin còn mở sau đối soát; tỷ lệ trùng sau gộp; tỷ lệ trường CV được ứng viên sửa; thời gian từ lúc nguồn đóng tin đến lúc kết quả biến mất; số nguồn đang có quyền khai thác hợp lệ. Các mốc cụ thể chỉ được đặt sau khi có dữ liệu thử nghiệm, tránh trình bày mục tiêu như số liệu đã đạt.")
para("Đối với dữ liệu cá nhân tại Việt Nam, thiết kế phải được rà soát theo Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP, đều có hiệu lực từ 01/01/2026 [S7][S8]. Thực tế triển khai cần xác định mục đích xử lý, thông báo và ghi nhận lựa chọn của ứng viên, quyền xem/sửa/xóa, thời hạn giữ CV và bản sao, phân quyền nhà tuyển dụng, xử lý nhà cung cấp dịch vụ và truyền dữ liệu xuyên biên giới nếu có. Đây là yêu cầu thiết kế cần thẩm định pháp lý trước vận hành, không phải tuyên bố hệ thống đã tuân thủ.")

para("2.6. Tài liệu chính thức dùng để kiểm chứng Phần 2", heading=True)
for source in [
    "[S1] LinkedIn Talent Solutions, Job Posting API Overview: https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/sync-job-postings",
    "[S2] Indeed Partner Docs, Job Sync API: https://docs.indeed.com/job-sync-api",
    "[S3] Google Search Central, JobPosting structured data: https://developers.google.com/search/docs/appearance/structured-data/job-posting",
    "[S4] GitHub Docs, Choosing permissions for a GitHub App: https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app",
    "[S5] European Commission, Download ESCO: https://esco.ec.europa.eu/en/use-esco/download",
    "[S6] O*NET Resource Center, O*NET Database: https://www.onetcenter.org/database.html",
    "[S7] Chính phủ Việt Nam, Luật 91/2025/QH15: https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=",
    "[S8] Chính phủ Việt Nam, Nghị định 356/2025/NĐ-CP: https://vanban.chinhphu.vn/?classid=1&docid=216387&pageid=27160",
    "[S9] LinkedIn, Getting Access to LinkedIn APIs: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access",
    "[S10] Indeed Partner Docs, API guides: https://docs.indeed.com/api-guides/",
    "[S11] TopCV, Điều khoản sử dụng dịch vụ với nhà tuyển dụng: https://tuyendung.topcv.vn/term-of-services",
    "[S12] ITviec, Quy chế hoạt động: https://itviec.com/blog/quy-che-hoat-dong-cua-itviec/",
]:
    para(source, small=True)
para("Ngày kiểm chứng tài liệu trực tuyến: 23/10/2026. Quyền đối với từng feed thương mại vẫn phải xác nhận bằng hợp đồng và tài liệu API do đối tác cấp.", small=True)

# Move the newly generated elements from the end to the gap before Part 3.
for element in added:
    body.remove(element)
    end._p.addprevious(element)

# Correct only downstream statements that would contradict the researched section.
for p in doc.paragraphs:
    if p.text.startswith("Bước 1.1: Hệ thống Scrapy và API Consumer kéo dữ liệu"):
        p.text = ("Bước 1.1: Hệ thống nhận JD trực tiếp từ doanh nghiệp và feed/ATS đã cấp quyền; "
                  "nguồn website bên ngoài chỉ được nạp trong phạm vi thỏa thuận. LinkedIn/Indeed "
                  "không được giả định là API lấy tin công khai.")

checklist_table = next(t for t in doc.tables if t.rows[0].cells[0].text == "Hạng Mục Checklist")
for row in checklist_table.rows:
    if row.cells[0].text.startswith("Mục 2:"):
        row.cells[1].text = "Phân tích nguồn dữ liệu đầu vào, quyền sử dụng, trường dữ liệu và tính khả thi từng nguồn."
        row.cells[2].text = "Ma trận 7 nhóm nguồn theo ưu tiên P0–P2; phân biệt feed được cấp quyền với API đăng tin LinkedIn/Indeed; bổ sung từ điển trường, provenance và rủi ro."
        row.cells[3].text = "Phần 2 và Phụ lục B; bảng so sánh nguồn và tài liệu [S1]–[S12]"

dictionary_table = next(t for t in doc.tables if t.rows[0].cells[0].text == "Nguồn")
for row in dictionary_table.rows:
    if row.cells[0].text.startswith("API / feed việc làm"):
        row.cells[0].text = "JD trực tiếp / ATS / feed có quyền"
        row.cells[3].text = "Chỉ sử dụng trong phạm vi thỏa thuận; không coi API đăng tin LinkedIn/Indeed là API lấy JD đầu vào."
    if row.cells[0].text.startswith("Website tuyển dụng"):
        row.cells[0].text = "Website tuyển dụng có thỏa thuận"
        row.cells[3].text = "Có quyền thu thập, lưu và hiển thị; không vượt kiểm soát truy cập; gỡ khi hết quyền hoặc tin đóng."
    if row.cells[0].text.startswith("GitHub qua OAuth"):
        row.cells[0].text = "GitHub App / repo được ứng viên chọn"
        row.cells[3].text = "Quyền đọc tối thiểu; không lấy toàn bộ mã theo mặc định; không suy diễn năng lực từ số commit."

for p in doc.paragraphs:
    if p.text.startswith("6. Chính phủ Việt Nam. Nghị định số 13/2023"):
        p.text = ("6. Chính phủ Việt Nam. Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và "
                  "Nghị định 356/2025/NĐ-CP (hiệu lực 01/01/2026). "
                  "https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup= ; "
                  "https://vanban.chinhphu.vn/?classid=1&docid=216387&pageid=27160")
    if p.text.startswith("Ngày truy cập các nguồn trực tuyến: 22/10/2026"):
        p.text = ("Ngày kiểm chứng các nguồn trực tuyến cho Phần 2: 23/10/2026. "
                  "Với API tuyển dụng thương mại, cần văn bản quyền truy cập/điều khoản từng đối tác trước khi triển khai.")

doc.save(OUTPUT_PATH)
print(OUTPUT_PATH)
print("Part 2 body elements:", len(added))
