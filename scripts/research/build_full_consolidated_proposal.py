"""Build the full, nonduplicative proposal from the three existing Word drafts."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK, WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "research"
SOURCE = DOCS / "De_Xuat_He_Thong_Tim_Viec_Thong_Minh_Chi_Tiet.docx"
OUTPUT = DOCS / "De_Xuat_UniTalent_AI_Tong_Hop.docx"


def para(doc, text="", style=None):
    p = doc.add_paragraph(style=style)
    p.add_run(text)
    p.paragraph_format.keep_together = True
    return p


def bullet(doc, text):
    return para(doc, text, "List Bullet")


def heading(doc, text, level=2):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.width = Inches(widths[j])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.text = h
        for p in cell.paragraphs:
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCECE8")
        cell._tc.get_or_add_tcPr().append(shd)
    header_props = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header_props.append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for j, value in enumerate(row):
            cells[j].width = Inches(widths[j])
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cells[j].text = value
            for p in cells[j].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                for run in p.runs:
                    run.font.size = Pt(8.7)
        cant_split = OxmlElement("w:cantSplit")
        t.rows[-1]._tr.get_or_add_trPr().append(cant_split)
    return t


def remove_opening_metadata(doc):
    course_line = next(
        (p for p in doc.paragraphs
         if p.text.strip().startswith("Học phần: Hệ Thống Kinh Doanh Thông Minh")),
        None,
    )
    if course_line is not None:
        course_line._p.getparent().remove(course_line._p)

    opening_box = next(
        (t for t in doc.tables
         if "MỤC TIÊU & TÔN CHỈ THIẾT KẾ" in t.cell(0, 0).text),
        None,
    )
    if opening_box is not None:
        following = opening_box._tbl.getnext()
        opening_box._tbl.getparent().remove(opening_box._tbl)
        if (
            following is not None
            and following.tag == qn("w:p")
            and not following.xpath(".//w:t")
            and not following.xpath(".//w:br")
        ):
            following.getparent().remove(following)


def build():
    if not SOURCE.exists():
        doc = Document(OUTPUT)
        remove_opening_metadata(doc)
        doc.save(OUTPUT)
        print(OUTPUT)
        return

    doc = Document(SOURCE)
    opening = doc.tables[0].cell(0, 0)
    for p in opening.paragraphs:
        for run in p.runs:
            run.text = run.text.replace(
                "bám sát 100% Checklist 4 mục tiêu chuẩn của đề bài",
                "trình bày đủ 4 yêu cầu trong checklist của đề bài",
            )
    doc.tables[1].cell(1, 4).text = "Theo quyền API"
    doc.tables[1].cell(2, 4).text = "Theo thỏa thuận"
    checklist = doc.tables[4]
    checklist.cell(0, 3).text = "Minh chứng trong tài liệu"
    for p in checklist.cell(0, 3).paragraphs:
        for run in p.runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9)
    for row, label in enumerate(
        (
            "Đã mô tả đối tượng và tính năng đề xuất",
            "Đã phân tích 6 nhóm nguồn dữ liệu",
            "Đã đặc tả pipeline và kiểm soát chất lượng",
            "Đã vẽ DFD và mô tả 4 luồng chính",
        ),
        start=1,
    ):
        checklist.cell(row, 3).text = label
    for p in doc.paragraphs:
        if p.text.startswith("a) Nguồn API Tuyển dụng Quốc tế"):
            p.text = (
                "a) Nguồn API tuyển dụng quốc tế (LinkedIn, Indeed): Nếu được đối tác cấp quyền truy cập, "
                "hệ thống có thể nhận Job ID, chức danh, công ty, ngành, mô tả, loại hình và địa điểm. "
                "Độ đầy đủ và tin cậy phải đo theo từng nguồn. Chu kỳ đồng bộ được xác định theo hợp đồng, "
                "giới hạn API và yêu cầu về độ mới của tin."
            )
        elif p.text.startswith("Cơ chế Ingestion: Triển khai kiến trúc kết hợp"):
            p.text = (
                "Cơ chế Ingestion: Nạp theo lô bằng bộ lập lịch với tần suất được phép của từng nguồn; "
                "sự kiện phát sinh khi ứng viên tải CV, cập nhật hồ sơ hoặc nộp đơn được xử lý qua hàng đợi. "
                "Nếu quy mô tăng, có thể dùng Airflow để điều phối và Kafka cho luồng sự kiện; "
                "ghi source_id, run_id và thời điểm ở cả hai nhánh."
            )
        elif p.text.startswith("Bản đề xuất 'Hệ Thống Tìm Kiếm Việc Làm Thông Minh"):
            p.text = (
                "Bản đề xuất mô tả cách kết nối ứng viên đầu sự nghiệp với nhà tuyển dụng bằng dữ liệu "
                "có nguồn gốc rõ ràng, quy trình làm sạch, so khớp có giải thích và báo cáo BI. "
                "Tính khả thi của từng tính năng phụ thuộc vào quyền sử dụng nguồn dữ liệu, chất lượng CV/JD, "
                "đánh giá mô hình và thử nghiệm thực tế. Giai đoạn đầu nên triển khai MVP, đo baseline "
                "rồi mới mở rộng các chức năng AI phức tạp."
            )

    remove_opening_metadata(doc)

    old_body = list(doc.element.body)
    refs_heading = next(p for p in doc.paragraphs if p.text.startswith("G. Tài liệu tham khảo"))
    refs_heading.text = "K. Tài liệu tham khảo kỹ thuật và dữ liệu"

    heading(doc, "H. Bối cảnh và khoảng trống của giải pháp", 2)
    para(doc, "Bản nghiên cứu mở rộng chỉ ra ba vấn đề cần giải quyết khi kết nối sinh viên mới ra trường với doanh nghiệp: ứng viên thiếu lịch sử việc làm để chứng minh năng lực; nhà tuyển dụng khó sàng lọc khối lượng CV lớn; và hai bên thiếu phản hồi đủ cụ thể để cải thiện lựa chọn. Vì vậy hệ thống cần ghi nhận bằng chứng năng lực từ dự án, minh bạch lý do gợi ý và giữ con người trong quyết định tuyển dụng.")
    table(doc, ["Nhóm", "Vấn đề cần xử lý", "Cách hệ thống đáp ứng"], [
        ("Ứng viên", "CV ít kinh nghiệm; không biết kỹ năng nào đang thiếu; khó theo dõi trạng thái đơn.", "Phân tích CV có bước xác nhận; kết nối dự án do ứng viên chọn; nêu kỹ năng trùng/thiếu; lưu lịch sử ứng tuyển và phản hồi."),
        ("Nhà tuyển dụng", "JD không nhất quán; mất thời gian lọc CV; khó kiểm chứng dự án kỹ thuật.", "Biểu mẫu JD có must-have/nice-to-have; danh sách ứng viên có giải thích; liên kết bằng chứng dự án và trạng thái kiểm tra rõ ràng."),
        ("Vận hành", "Tin trùng, tin hết hạn và tin nghi vấn làm giảm độ tin cậy của kết quả.", "Xác minh đơn vị đăng tuyển; khử trùng lặp, kiểm tra hạn/URL; hàng đợi kiểm duyệt và nhật ký thay đổi."),
    ], [1.05, 2.65, 3.18])
    heading(doc, "H.1 Điểm khác biệt và phạm vi chứng minh", 3)
    para(doc, "UniTalent AI ưu tiên phân khúc thực tập sinh và nhân sự đầu sự nghiệp. Điểm khác biệt đề xuất là dùng kỹ năng, dự án, điều kiện làm việc và lịch học do ứng viên tự cung cấp thay cho việc xem số năm kinh nghiệm như tín hiệu duy nhất. Hệ thống có thể đề xuất kế hoạch học tập ngắn theo kỹ năng còn thiếu, nhưng kế hoạch đó là gợi ý; hoàn thành một bài tập hoặc có nhiều commit không tự động tương đương kinh nghiệm làm việc.")
    para(doc, "Các số liệu về tỷ lệ thất nghiệp, tỷ lệ phản hồi CV, thời gian tuyển, chi phí tuyển hoặc mức tăng hiệu quả trong bản nghiên cứu ban đầu chưa có bộ dữ liệu gốc và phương pháp tính đi kèm trong hồ sơ đề tài. Chúng là giả thuyết cần kiểm chứng, không được trình bày như kết quả thực nghiệm của UniTalent AI. KPI trong phần sau được định nghĩa để có thể đo trong giai đoạn pilot.")

    heading(doc, "I. Thiết kế chức năng mở rộng và trải nghiệm hai vai trò", 2)
    para(doc, "Các chức năng dưới đây tổng hợp nội dung riêng của báo cáo nghiên cứu với hành trình ứng viên/nhà tuyển dụng ở Phụ lục A. Chúng được chia theo độ ưu tiên để phạm vi MVP đủ khả thi; các tính năng AI phức tạp cần dữ liệu đánh giá và quyền sử dụng rõ ràng trước khi đưa vào vận hành.")
    table(doc, ["Phân hệ", "Đầu vào và xử lý", "Đầu ra / giới hạn"], [
        ("Hồ sơ và CV", "Ứng viên tải CV, chọn quyền hiển thị, xác nhận kỹ năng, học vấn, dự án và lịch rảnh do hệ thống trích xuất.", "Hồ sơ có nguồn từng trường; ứng viên sửa được lỗi. CV gốc chỉ mở cho người có quyền."),
        ("Gợi ý việc làm", "Lọc điều kiện bắt buộc; truy hồi từ khóa + vector; tính điểm từng thành phần; kiểm tra nguồn và hạn tin.", "Danh sách xếp hạng có lý do, kỹ năng thiếu và trạng thái dữ liệu; AI không tự từ chối ứng viên."),
        ("Phân tích dự án", "Ứng viên chọn repo công khai hoặc cấp OAuth tối thiểu; đọc README, ngôn ngữ, cấu trúc và bằng chứng kiểm thử.", "Tóm tắt bằng chứng để HR xem lại; cảnh báo chất lượng mã hoặc khả năng sao chép chỉ là tín hiệu, không cấp chứng nhận chắc chắn."),
        ("Gợi ý học tập", "Đối chiếu kỹ năng bắt buộc/ưu tiên trong JD với hồ sơ đã xác nhận và taxonomy phiên bản cụ thể.", "Danh sách kỹ năng cần bổ sung, tài liệu tham khảo và bước học đề xuất; người dùng quyết định có theo hay không."),
        ("Luyện phỏng vấn", "Nếu triển khai giai đoạn sau: dùng JD làm ngữ cảnh đặt câu hỏi, lưu bản ghi khi ứng viên đồng ý.", "Phản hồi về nội dung câu trả lời và ví dụ cần cải thiện; không suy đoán tính cách/năng lực từ giọng nói hoặc khuôn mặt."),
    ], [1.22, 2.91, 2.75])
    heading(doc, "I.1 Luồng giao diện ứng viên", 3)
    bullet(doc, "Bảng tin việc làm hiển thị bộ lọc địa điểm, loại hình, lương nếu có, hạn nộp và lý do gợi ý. Điểm phù hợp phải đi kèm các thành phần và chú thích rằng đây là điểm hỗ trợ tìm kiếm.")
    bullet(doc, "Trang hồ sơ cho xem CV gốc, trường trích xuất, dự án đã chọn chia sẻ, lịch rảnh và quyền riêng tư. Ứng viên xem trước bản hồ sơ nhà tuyển dụng sẽ nhận.")
    bullet(doc, "Trang ứng tuyển lưu bản CV cụ thể đã gửi, thời gian gửi, trạng thái xử lý và phản hồi của nhà tuyển dụng. Mỗi thay đổi trạng thái cần có lịch sử để tránh mất dấu.")
    heading(doc, "I.2 Luồng giao diện nhà tuyển dụng", 3)
    bullet(doc, "Biểu mẫu JD tách yêu cầu bắt buộc, ưu tiên, điều kiện làm việc, hạn tin và người phê duyệt. Hệ thống nhắc sửa JD thiếu thông tin hoặc tiêu chí mâu thuẫn.")
    bullet(doc, "Danh sách hồ sơ nêu lý do xếp hạng cùng bằng chứng gốc, độ tin cậy và dữ liệu còn thiếu. Nhà tuyển dụng lọc và quyết định từng vòng, không dùng điểm AI làm quy tắc loại tự động.")
    bullet(doc, "Bảng điều khiển tuyển dụng hiển thị phễu ứng tuyển, thời gian xử lý và nguồn ứng viên theo nhóm đủ lớn; quyền xem dữ liệu cá nhân tách khỏi quyền xem số liệu tổng hợp.")

    heading(doc, "J. Kiến trúc triển khai và đo lường kinh doanh thông minh", 2)
    heading(doc, "J.1 Chọn thành phần theo giai đoạn", 3)
    table(doc, ["Lớp", "MVP", "Khi mở rộng"], [
        ("Giao diện và API", "Giao diện web responsive; API quản lý tài khoản, CV, JD, tìm kiếm và đơn ứng tuyển.", "Tách dịch vụ có tải cao khi có số liệu vận hành; dùng hàng đợi cho OCR và phân tích mã nguồn."),
        ("Giao dịch và tệp", "PostgreSQL cho hồ sơ, tin và đơn; object storage mã hóa cho CV; sao lưu và phân quyền.", "Phân vùng dữ liệu, chính sách lưu/xóa theo loại và theo hợp đồng nguồn."),
        ("Tìm kiếm và AI", "Lọc có cấu trúc và từ khóa làm baseline; trích xuất kỹ năng có bước xác nhận.", "Thêm embedding, chỉ mục vector/hybrid search và đánh giá offline trước khi thay thứ tự kết quả."),
        ("Dữ liệu phân tích", "Ghi sự kiện tối thiểu và báo cáo tổng hợp từ dữ liệu đã giả danh.", "Kho phân tích riêng và mô hình hình sao khi khối lượng/truy vấn cần; giám sát chất lượng pipeline."),
    ], [1.15, 2.86, 2.87])
    para(doc, "Các công nghệ được nêu trong bản nghiên cứu (ví dụ Next.js, Spring Boot/FastAPI, Neo4j, ClickHouse, Qdrant, Kafka) là lựa chọn khả thi để đánh giá, không phải điều kiện bắt buộc phải triển khai đồng thời. Mỗi thành phần chỉ nên được thêm khi đáp ứng yêu cầu dữ liệu, tải, đội ngũ và chi phí; đồ thị kỹ năng đơn giản có thể bắt đầu bằng bảng quan hệ trước khi cần cơ sở dữ liệu đồ thị.")
    heading(doc, "J.2 Định nghĩa KPI để tránh tuyên bố hiệu quả chưa đo", 3)
    table(doc, ["KPI", "Cách tính đề xuất", "Điều kiện diễn giải"], [
        ("Độ mới tin", "Tỷ lệ tin còn hiệu lực có lần kiểm tra nguồn trong ngưỡng thời gian đã công bố.", "Báo theo nguồn và kỳ; tin không truy cập được cần tách khỏi tin còn hạn."),
        ("Tỷ lệ trùng", "Số tin bị gộp / tổng tin thô được nạp trong kỳ.", "Kiểm tra thủ công mẫu để ước lượng gộp nhầm và sót trùng."),
        ("Precision@K / nDCG@K", "Đánh giá thứ tự kết quả trên tập CV-JD được người có chuyên môn gán nhãn.", "So với baseline lọc/từ khóa; nêu K, số cặp và độ nhất quán nhãn."),
        ("Tỷ lệ chuyển vòng", "Số đơn được mời vòng tiếp / số đơn hợp lệ trong cùng cohort.", "Báo theo ngành, vị trí và giai đoạn; không quy toàn bộ thay đổi cho AI."),
        ("Time-to-fill", "Ngày nhận việc trừ ngày tin được duyệt đăng đối với vị trí đã tuyển xong.", "Tách tin đóng không tuyển được; nêu trung vị và kích thước mẫu."),
    ], [1.12, 2.88, 2.88])
    para(doc, "Bảng FACT_APPLICATION trong mô hình hình sao giữ một dòng cho một lần ứng tuyển. Các mốc phỏng vấn, đề nghị và nhận việc có thể là bảng sự kiện riêng hoặc các trường thời điểm được định nghĩa thống nhất. DIM_STUDENT, DIM_JOB, DIM_COMPANY và DIM_TIME phục vụ lát cắt phân tích; JOB_SKILL là bảng cầu nối để không nhân đôi số đơn khi tổng hợp theo kỹ năng. Mọi dashboard phải chỉ rõ thời kỳ, số mẫu, bộ lọc và trạng thái dữ liệu đến thời điểm cập nhật.")
    heading(doc, "J.3 Dòng dữ liệu từ nguồn đến kết quả", 3)
    para(doc, "DFD ở Phần 4 và Phụ lục E thể hiện kiến trúc tổng thể. Khi triển khai, mỗi luồng phải có khóa truy vết: source_id và run_id ở bước nạp; canonical_job_id hoặc profile_id sau khử trùng lặp; model_version khi trích xuất/nhúng; request_id khi tìm kiếm; application_id khi nộp đơn. Các khóa này cho phép kiểm tra vì sao một tin hoặc hồ sơ xuất hiện, bị ẩn hoặc được xếp hạng tại một thời điểm.")
    bullet(doc, "Luồng việc làm: nguồn được phép → bản thô có nguồn gốc → kiểm tra và chuẩn hóa → kho JD hợp lệ → chỉ mục tìm kiếm → kết quả có đường dẫn nguồn.")
    bullet(doc, "Luồng ứng viên: đồng ý và tải CV/chọn dự án → bản gốc bảo vệ theo quyền → trích xuất có độ tin cậy → người dùng sửa/xác nhận → hồ sơ phục vụ so khớp.")
    bullet(doc, "Luồng phản hồi: tìm kiếm → xem/lưu/ứng tuyển → trạng thái do nhà tuyển dụng cập nhật → sự kiện giả danh → KPI và tập đánh giá; quyền xóa hoặc rút đồng ý phải lan đến chỉ mục và kho phân tích theo chính sách.")

    body = doc.element.body
    current = list(body)
    reference_index = current.index(refs_heading._p)
    sect = body.sectPr
    new_elements = [el for el in current if el not in old_body and el is not sect]
    for offset, element in enumerate(new_elements):
        body.remove(element)
        body.insert(reference_index + offset, element)

    doc.core_properties.title = "Đề xuất hệ thống tìm việc thông minh và chiến lược thu thập dữ liệu"
    doc.core_properties.subject = "Bản tổng hợp chi tiết từ đề xuất ban đầu, đề xuất mở rộng và báo cáo nghiên cứu"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
