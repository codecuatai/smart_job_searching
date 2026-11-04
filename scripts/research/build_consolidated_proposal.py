from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "research"
DIAGRAMS = ROOT / "docs" / "diagrams"
OUT = DOCS / "De_Xuat_UniTalent_AI_Tong_Hop.docx"

NAVY = "173A32"
GREEN = "247A5B"
MINT = "EAF3EC"
PALE = "F4F7F4"
INK = "26352D"
MUTED = "58665D"
LINE = "D7E0D9"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=105, bottom=90, end=105):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=LINE, size="5"):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def remove_paragraph_borders(paragraph_properties):
    if paragraph_properties is not None:
        border = paragraph_properties.find(qn("w:pBdr"))
        if border is not None:
            paragraph_properties.remove(border)


def set_run_font(run, size=10.5, bold=False, color=INK, name="Aptos"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_para(doc, text, style=None, bold_lead=None, after=5, size=10.5, color=INK):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.12
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        set_run_font(r, size=size, bold=True, color=color)
        r = p.add_run(text[len(bold_lead):])
        set_run_font(r, size=size, color=color)
    else:
        r = p.add_run(text)
        set_run_font(r, size=size, color=color)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.left_indent = Inches(0.22 + 0.18 * level)
    p.paragraph_format.first_line_indent = Inches(-0.12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.08
    r = p.add_run(text)
    set_run_font(r, 10.1)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(11 if level == 1 else 7)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text)
    set_run_font(r, 14 if level == 1 else 11.5, True, NAVY if level == 1 else GREEN)
    return p


def add_table(doc, headers, rows, widths, font_size=8.7):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = Inches(widths[i])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, NAVY)
        set_cell_margins(cell, 95, 110, 95, 110)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(header)
        set_run_font(r, font_size, True, "FFFFFF")
    set_repeat_table_header(table.rows[0])
    prevent_row_split(table.rows[0])
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        prevent_row_split(table.rows[-1])
        for ci, value in enumerate(row):
            cell = cells[ci]
            cell.width = Inches(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if ri % 2 == 1:
                set_cell_shading(cell, PALE)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.02
            r = p.add_run(value)
            set_run_font(r, font_size, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_figure(doc, filename, caption, width=7.05):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(DIAGRAMS / filename), width=Inches(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)
    c.paragraph_format.keep_with_next = True
    r = c.add_run(caption)
    set_run_font(r, 8.5, False, MUTED)


def add_page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for item in (begin, instr, separate, text, end):
        run._r.append(item)
    set_run_font(run, 8.5, color=MUTED)


def setup_doc(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.62)
    section.bottom_margin = Inches(0.62)
    section.left_margin = Inches(0.68)
    section.right_margin = Inches(0.68)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.3)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(INK)
    for name, size, color in (("Heading 1", 14, NAVY), ("Heading 2", 11.5, GREEN)):
        st = styles[name]
        st.font.name = "Aptos Display"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos Display")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
    remove_paragraph_borders(styles["Title"]._element.pPr)
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = header.add_run("UNITALENT AI  |  ĐỀ XUẤT HỆ THỐNG")
    set_run_font(r, 8.2, True, GREEN)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = footer.add_run("Bản tổng hợp đề xuất  •  Trang ")
    set_run_font(r, 8.5, color=MUTED)
    add_page_field(footer)


def build():
    doc = Document()
    setup_doc(doc)

    title = doc.add_paragraph(style="Title")
    remove_paragraph_borders(title._p.pPr)
    title.paragraph_format.space_before = Pt(22)
    title.paragraph_format.space_after = Pt(5)
    r = title.add_run("Đề xuất hệ thống tìm việc thông minh UniTalent AI")
    set_run_font(r, 24, True, NAVY, "Aptos Display")
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(13)
    r = subtitle.add_run("Bản tổng hợp: đối tượng, tính năng, nguồn dữ liệu và luồng vận hành")
    set_run_font(r, 11.5, False, MUTED)

    add_heading(doc, "Tóm tắt đề xuất", 1)
    add_para(doc, "UniTalent AI là hệ thống kết nối sinh viên, thực tập sinh và ứng viên mới tốt nghiệp với nhà tuyển dụng. Hệ thống kết hợp tìm kiếm theo điều kiện, so khớp ngữ nghĩa và bằng chứng năng lực từ CV, dự án, kỹ năng và sở thích. Kết quả luôn kèm lý do gợi ý để người dùng tự quyết định; điểm AI không tự động loại hồ sơ.")
    add_para(doc, "Phạm vi bản đề xuất tập trung vào bốn yêu cầu của bài: xác định người dùng và chức năng thông minh; mô tả nguồn cùng trường dữ liệu; trình bày thu thập, làm sạch, lưu trữ và kiểm soát chất lượng; minh họa luồng dữ liệu từ nguồn đến kết quả.")

    add_heading(doc, "1. Đối tượng mục tiêu và chức năng", 1)
    add_table(doc, ["Người dùng", "Nhu cầu", "Chức năng và đầu ra"], [
        ("Sinh viên / fresher", "Tìm việc phù hợp dù chưa có lịch sử làm việc dài; biết mình còn thiếu gì.", "Tạo hồ sơ từ CV; trích xuất kỹ năng; gợi ý việc có giải thích; lọc theo địa điểm, lịch, hình thức và lương; chẩn đoán kỹ năng thiếu; theo dõi ứng tuyển."),
        ("Nhà tuyển dụng", "Giảm thời gian xem hồ sơ và tìm ứng viên phù hợp với tiêu chí vị trí.", "Tạo JD có kỹ năng bắt buộc/ưu tiên; xem danh sách xếp hạng kèm bằng chứng; lọc theo tiêu chí; quản lý trạng thái ứng tuyển; xem báo cáo tuyển dụng tổng hợp."),
        ("Quản trị / vận hành", "Giữ dữ liệu chính xác, tin tuyển dụng đáng tin cậy và quyền truy cập phù hợp.", "Quản lý nguồn dữ liệu; kiểm duyệt tin nghi vấn; theo dõi độ mới/chất lượng; xử lý yêu cầu sửa, tải xuống hoặc xóa dữ liệu."),
    ], [1.28, 2.42, 3.38], 8.7)
    add_para(doc, "Nguyên tắc thiết kế: tiêu chí bắt buộc được kiểm tra riêng; mô hình xếp hạng chỉ hỗ trợ quyết định; người dùng có thể sửa dữ liệu trích xuất sai; dữ liệu nhạy cảm không dùng làm tín hiệu xếp hạng.", after=7)

    add_heading(doc, "2. Nguồn dữ liệu và cách thu thập", 1)
    add_para(doc, "Mỗi bản ghi cần lưu nguồn gốc, thời điểm lấy, phiên bản và trạng thái quyền sử dụng. Chỉ tích hợp API, feed, dữ liệu do đối tác cấp hoặc dữ liệu người dùng chủ động cung cấp. Không mặc định LinkedIn, Indeed hay cổng việc làm khác cho phép API; không thu thập tự động trái điều khoản. Khi chưa có quyền tích hợp, nhà tuyển dụng có thể nhập JD hoặc người dùng chuyển tới trang đăng tuyển gốc.")
    add_table(doc, ["Nguồn", "Trường dữ liệu chính", "Kênh / nhịp / kiểm soát"], [
        ("Hồ sơ ứng viên", "CV; học vấn; kỹ năng; dự án; chứng chỉ; sở thích; địa điểm; lịch rảnh; quyền hiển thị.", "Tải lên trực tiếp và đồng ý xử lý. Cập nhật khi người dùng sửa. CV gốc mã hóa, truy cập theo quyền."),
        ("Tin tuyển dụng và JD", "Tiêu đề; mô tả; kỹ năng bắt buộc/ưu tiên; cấp bậc; địa điểm; hình thức; lương nếu có; hạn nộp; URL gốc.", "API/feed có cấp phép, đối tác ATS hoặc nhập từ nhà tuyển dụng. Đồng bộ theo lịch từng nguồn; kiểm tra hết hạn và URL."),
        ("Hồ sơ doanh nghiệp", "Tên pháp nhân; ngành; website; địa điểm; trạng thái xác minh; người đăng và quyền đăng.", "Nhà tuyển dụng cung cấp; quản trị xác minh theo quy trình. Không công khai thông tin liên hệ cá nhân nếu chưa được phép."),
        ("Dự án / GitHub", "Tên dự án; ngôn ngữ; README; metadata repo; liên kết; bằng chứng người dùng chọn chia sẻ.", "Người dùng nhập URL hoặc OAuth với quyền tối thiểu. Không truy cập repo riêng ngoài phạm vi được cấp; không coi số commit là năng lực độc lập."),
        ("Taxonomy kỹ năng", "Tên chuẩn; bí danh; mã nghề/kỹ năng; nhóm và quan hệ tương đương.", "ESCO/O*NET hoặc bộ từ điển được cấp phép; tải theo phiên bản định kỳ và ghi rõ nguồn/phiên bản."),
        ("Sự kiện sử dụng", "Lượt xem; lưu; nhấp; ứng tuyển; trạng thái phỏng vấn/nhận việc; thời điểm và mã giả danh.", "Ghi sự kiện phát sinh; chỉ dùng mục đích vận hành/đánh giá đã thông báo; tổng hợp hoặc giả danh trước BI."),
    ], [1.22, 2.78, 3.08], 8.2)

    add_heading(doc, "3. Thu thập, làm sạch và lưu trữ", 1)
    add_para(doc, "Quy trình ETL/ELT đề xuất gồm năm bước. Bản gốc được giữ tách biệt khỏi bản chuẩn hóa để có thể truy vết và chạy lại khi thay đổi bộ trích xuất hoặc taxonomy.")
    add_figure(doc, "diagram_etl_detailed.png", "Hình 1. Pipeline tiếp nhận, kiểm tra, chuẩn hóa, làm giàu và phát hành dữ liệu.", 7.0)
    add_table(doc, ["Bước", "Xử lý chính", "Điều kiện trước khi đưa vào tìm kiếm"], [
        ("1. Tiếp nhận", "Ghi source_id, fetched_at, run_id, URL và phiên bản; retry có giới hạn; chống ghi lặp.", "Nguồn được phép; có thể truy vết; phân loại dữ liệu và quyền sử dụng."),
        ("2. Kiểm tra", "Kiểm tra schema, kiểu dữ liệu, trường bắt buộc, định dạng URL, ngày hết hạn và mức đầy đủ.", "Bản ghi lỗi được cách ly, có lỗi cụ thể; không làm hỏng lô dữ liệu hợp lệ."),
        ("3. Chuẩn hóa", "Chuẩn Unicode/HTML; chuẩn địa danh, tiền tệ, loại hình; loại trùng theo URL và dấu vân tay JD.", "Giữ bản gốc; không tự điền thông tin không có trong nguồn; ghi lịch sử thay đổi."),
        ("4. Làm giàu", "Trích xuất kỹ năng từ CV/JD; ánh xạ taxonomy; tạo vector; lưu confidence và model_version.", "Kết quả dưới ngưỡng tin cậy được gắn cờ để sửa hoặc kiểm duyệt."),
        ("5. Phát hành", "Cập nhật kho giao dịch, chỉ mục tìm kiếm và sự kiện phân tích; theo dõi freshness và lỗi.", "Tin hết hạn bị ẩn; chỉ phát hành bản hợp lệ; có audit log và khả năng replay."),
    ], [1.0, 3.05, 3.03], 8.2)
    add_para(doc, "Kho dữ liệu đề xuất: PostgreSQL lưu hồ sơ/JD/trạng thái ứng tuyển; object storage mã hóa lưu CV gốc với thời hạn; chỉ mục vector phục vụ tìm kiếm ngữ nghĩa và luôn giữ metadata nguồn; kho phân tích lưu sự kiện đã giả danh. Quyền truy cập phân vai, audit log, sao lưu và quy trình xóa cần áp dụng xuyên suốt vòng đời dữ liệu.", after=6)

    add_heading(doc, "4. Luồng tìm kiếm và chấm điểm phù hợp", 1)
    add_para(doc, "Khi người dùng tìm việc, hệ thống xác thực quyền xem hồ sơ, lọc trước theo trạng thái tin và điều kiện người dùng chọn, sau đó lấy ứng viên bằng tìm kiếm từ khóa/ngữ nghĩa. Bộ xếp hạng tính điểm đa tiêu chí và trả lại giải thích, độ tin cậy, nguồn tin cùng thời điểm cập nhật.")
    add_figure(doc, "diagram_matching_detailed.png", "Hình 2. Luồng so khớp ứng viên – công việc và các yếu tố cấu thành điểm gợi ý.", 7.0)
    add_para(doc, "Công thức khởi điểm trong đề xuất: Match = 0,45 × độ phủ kỹ năng + 0,30 × tương đồng ngữ nghĩa + 0,15 × bằng chứng dự án + 0,10 × phù hợp sở thích. Các trọng số chỉ là cấu hình giả thuyết để thử nghiệm, chưa phải kết quả đo lường. Điều kiện bắt buộc như địa điểm, hình thức hoặc trạng thái còn tuyển được áp dụng trước xếp hạng; trường không có dữ liệu phải được hiển thị là chưa biết, không tự coi là không đạt.")
    add_para(doc, "Với mỗi kết quả, giao diện nên nêu 2–3 lý do có bằng chứng (ví dụ kỹ năng trùng, dự án liên quan), kỹ năng còn thiếu, hạn đăng và liên kết nguồn. Mô hình cần được đánh giá theo nhóm ngành/trường và rà soát sai lệch; nhà tuyển dụng vẫn xem hồ sơ và ra quyết định cuối.")

    add_heading(doc, "5. Sơ đồ luồng dữ liệu tổng thể", 1)
    p = add_para(doc, "DFD dưới đây mô tả hai chiều dữ liệu: dữ liệu nguồn đi vào kho và dịch vụ AI/BI; truy vấn người dùng đi qua bộ tìm kiếm để trả về kết quả; sự kiện ứng tuyển được ghi lại phục vụ theo dõi và phân tích.")
    p.paragraph_format.keep_with_next = True
    add_figure(doc, "dfd_data_flow_detailed.png", "Hình 3. DFD cấp 1 từ nguồn dữ liệu đến người dùng và nhà tuyển dụng.", 7.0)
    add_heading(doc, "Các kho dữ liệu và phân tích BI", 2)
    add_para(doc, "Giao dịch ứng tuyển được nạp vào mô hình hình sao để phân tích theo ứng viên, công việc, doanh nghiệp, kỹ năng và thời gian. Bảng FACT_APPLICATION có grain là một dòng cho một lần ứng tuyển; bảng cầu nối JOB_SKILL xử lý quan hệ nhiều-nhiều giữa việc làm và kỹ năng.")
    add_figure(doc, "diagram_star_schema_detailed.png", "Hình 4. Mô hình BI hình sao và bảng cầu nối kỹ năng.", 5.55)
    add_para(doc, "Chỉ số nên tính từ dữ liệu thực tế sau khi có mẫu đủ tin cậy: thời gian từ đăng tin đến tuyển; tỷ lệ qua vòng trên số ứng viên được xem; tỷ lệ ứng tuyển theo nhóm điểm; tỷ lệ tin còn hiệu lực; và kỹ năng được yêu cầu theo ngành/thời gian. Báo cáo chỉ hiển thị dữ liệu tổng hợp, áp dụng ngưỡng nhóm tối thiểu để giảm nguy cơ nhận diện cá nhân.")

    add_heading(doc, "6. Triển khai và tiêu chí đánh giá", 1)
    add_table(doc, ["Giai đoạn", "Phạm vi", "Cách đánh giá"], [
        ("MVP", "Hồ sơ ứng viên, nhập JD/nguồn feed được phép, lọc điều kiện, tìm kiếm từ khóa và giải thích cơ bản.", "Độ đầy đủ trường bắt buộc; độ mới tin; tỷ lệ trùng; thời gian trả kết quả; kiểm thử quyền truy cập."),
        ("Pilot", "Thêm trích xuất kỹ năng, semantic matching, phản hồi người dùng và bảng BI cơ bản.", "Precision@K / nDCG@K trên bộ đánh giá có gán nhãn; tỷ lệ nhấp/lưu/ứng tuyển; kiểm tra theo nhóm và đánh giá của người dùng."),
        ("Mở rộng", "Thêm đối tác dữ liệu, taxonomy nhiều ngành, phân tích phễu và cảnh báo chất lượng.", "So sánh với baseline; giám sát drift, freshness, lỗi nguồn và tỷ lệ kết quả bị báo sai; chỉ đặt mục tiêu số sau khi có baseline."),
    ], [1.0, 3.12, 2.96], 8.4)
    add_heading(doc, "Kết luận", 2)
    add_para(doc, "UniTalent AI giải quyết bài toán kết nối việc làm đầu sự nghiệp bằng cách kết hợp dữ liệu có nguồn gốc rõ ràng, chuẩn hóa kỹ năng, tìm kiếm ngữ nghĩa và giải thích kết quả. Tính khả thi phụ thuộc vào quyền truy cập nguồn việc làm, sự đồng ý của người dùng, chất lượng dữ liệu và đánh giá có kiểm soát; vì vậy nên bắt đầu bằng MVP có nguồn dữ liệu được cấp phép, đo baseline rồi mới mở rộng mô hình.")

    add_heading(doc, "Tài liệu tham khảo nền tảng", 1)
    refs = ("ESCO của European Commission: https://esco.ec.europa.eu/  •  "
            "O*NET Web Services: https://www.onetonline.org/  •  "
            "Reimers & Gurevych (2019), Sentence-BERT, EMNLP-IJCNLP: https://doi.org/10.18653/v1/D19-1410.\n"
            "Tin tuyển dụng bên ngoài chỉ kết nối khi có quyền phù hợp. KPI là chỉ số đề xuất đo lường, không phải kết quả thử nghiệm đã đạt.")
    p = add_para(doc, refs, after=3, size=8.7, color=MUTED)
    p.paragraph_format.line_spacing = 1.0

    doc.core_properties.title = "Đề xuất hệ thống tìm việc thông minh UniTalent AI"
    doc.core_properties.subject = "Bản tổng hợp đối tượng, dữ liệu, quy trình ETL và sơ đồ luồng dữ liệu"
    doc.core_properties.author = ""
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
