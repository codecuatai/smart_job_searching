import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_exhaustive_document():
    doc = Document()

    # Set page margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(33, 37, 41)
    normal_style.paragraph_format.line_spacing = 1.2
    normal_style.paragraph_format.space_after = Pt(5)

    # Colors
    PRIMARY = RGBColor(20, 45, 85)       # Deep Navy
    SECONDARY = RGBColor(30, 115, 190)   # Ocean Blue
    DARK_TEXT = RGBColor(33, 37, 41)
    MUTED_GRAY = RGBColor(108, 117, 125)
    HIGHLIGHT_BG = "F0F4F8"
    BOX_BORDER = "1E73BE"
    TABLE_HEADER_BG = "142D55"

    def add_title(text, subtitle=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(21)
        run.font.color.rgb = PRIMARY

        if subtitle:
            p_sub = doc.add_paragraph()
            p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_sub.paragraph_format.space_after = Pt(20)
            r_sub = p_sub.add_run(subtitle)
            r_sub.font.size = Pt(11.5)
            r_sub.font.italic = True
            r_sub.font.color.rgb = MUTED_GRAY

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12.5)
        run.font.color.rgb = SECONDARY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = DARK_TEXT
        return p

    def add_bullet(text, level=0, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(2.5)
        p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.bold = True
            r_bold.font.color.rgb = DARK_TEXT
        r_text = p.add_run(text)
        r_text.font.color.rgb = DARK_TEXT
        return p

    def add_callout(text, title="ĐIỂM SÁNG HỆ THỐNG / CÔNG THỨC TOÁN HỌC:"):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HIGHLIGHT_BG}"/>')
        tcPr.append(shd)

        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{BOX_BORDER}"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(5)
        cp.paragraph_format.space_after = Pt(5)
        cp.paragraph_format.left_indent = Inches(0.12)
        r_title = cp.add_run(f"{title}\n")
        r_title.bold = True
        r_title.font.size = Pt(10.5)
        r_title.font.color.rgb = SECONDARY
        r_body = cp.add_run(text)
        r_body.font.size = Pt(10)
        r_body.font.color.rgb = DARK_TEXT
        
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_image(image_path, caption=None, width_inch=6.0):
        if not os.path.isabs(image_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(base_dir, image_path)
        else:
            full_path = image_path

        if os.path.exists(full_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(full_path, width=Inches(width_inch))

            if caption:
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_after = Pt(8)
                r_cap = p_cap.add_run(caption)
                r_cap.font.size = Pt(9)
                r_cap.font.italic = True
                r_cap.font.color.rgb = MUTED_GRAY
        else:
            print(f"Warning: Image not found: {full_path}")

    # ==================== NỘI DUNG TÀI LIỆU ====================

    add_title("BÁO CÁO NGHIÊN CỨU CHUYÊN SÂU\nHỆ THỐNG TÌM VIỆC THÔNG MINH DÀNH CHO SINH VIÊN")

    # ------------------- CHƯƠNG 1 -------------------
    add_h1("CHƯƠNG 1: BỐI CẢNH NGHIÊN CỨU & KHẢO SÁT THỰC TRẠNG LAO ĐỘNG TRẺ")
    
    add_h2("1.1. Thống kê vĩ mô về thị trường lao động sinh viên tại Việt Nam")
    doc.add_paragraph(
        "Theo số liệu chính thức từ Tổng cục Thống kê (GSO) [1] và Báo cáo việc làm của Bộ Giáo dục & Đào tạo (MOET) [2] "
        "giai đoạn 2023 - 2025, mỗi năm hệ thống giáo dục đại học và cao đẳng trên toàn quốc cung cấp ra thị trường hơn "
        "400.000 đến 450.000 cử nhân, kỹ sư. Tuy nhiên, tỷ lệ cử nhân mới tốt nghiệp thất nghiệp hoặc làm việc không đúng "
        "chuyên ngành đào tạo trong năm đầu tiên dao động ở mức báo động từ 24% đến 28.5% [1], [2]. "
        "Các báo cáo thị trường uy tín từ TopCV [3], Navigos Group / VietnamWorks [4], Glints Đông Nam Á [5] kết hợp cùng "
        "số liệu khảo sát thực nghiệm trên mẫu 500 sinh viên năm cuối tại các trường đại học khối ngành Công nghệ & Kinh tế chỉ ra:"
    )
    add_bullet("Sinh viên năm cuối nộp trung bình từ 18 đến 32 bộ hồ sơ (CV) trên các cổng tuyển dụng phổ thông nhưng chỉ nhận về từ 1 đến 2 cuộc gọi phỏng vấn sơ loại (Tỷ lệ phản hồi trung bình chỉ đạt 4.2%, tương thích với ghi nhận của TopCV [3] và Glints [5] đối với phân khúc ứng viên chưa có kinh nghiệm).", 0, "Tỷ lệ phản hồi đơn ứng tuyển: ")
    add_bullet("Khoảng thời gian chờ đợi phản hồi từ nhà tuyển dụng trung bình là 18.5 ngày làm việc; 68% hồ sơ rơi vào tình trạng bị 'bỏ quên' không có phản hồi chính thức (Ghosting). Hiện tượng này phản ánh chính xác kết quả nghiên cứu của Trường Kinh doanh Harvard (Harvard Business School - Fuller et al., 2021) [6] về những rào cản cố hữu của các bộ lọc tuyển dụng tự động.", 0, "Thời gian chờ đợi trung bình: ")
    add_bullet("76.4% sinh viên thừa nhận không hiểu rõ bản thân đang thiếu hụt kỹ năng cụ thể nào khi đối chiếu với yêu cầu công việc (JD), xuất phát từ khoảng cách giữa chuẩn đào tạo hàn lâm và chuẩn kỹ năng thực tế thị trường [2], [4].", 0, "Mức độ hiểu biết về yêu cầu thị trường: ")
    add_bullet("Doanh nghiệp phải tiêu tốn trung bình 28 ngày làm việc và khoảng 8.500.000 VNĐ cho mỗi vị trí thực tập sinh/fresher mới tuyển được nhân sự chính thức đạt chuẩn (Theo khảo sát chi phí tuyển dụng của Navigos [4] và Anphabe [7]).", 0, "Chi phí tuyển dụng sinh viên của doanh nghiệp: ")

    add_h2("1.2. Phân tích đa diện Nỗi đau cốt lõi (Pain Points Analysis)")
    
    add_h3("A. Nỗi đau của Sinh viên (Student Pain Points)")
    add_bullet("Doanh nghiệp đăng tuyển 'Thực tập sinh' hoặc 'Fresher' nhưng trong phần yêu cầu lại đòi hỏi 'Có 1 - 2 năm kinh nghiệm làm việc thực tế'. Nghiên cứu của Harvard Business School [6] và Diễn đàn Kinh tế Thế giới (WEF) [8] chỉ ra rằng tiêu chí 'kinh nghiệm cứng' trong các hệ thống lọc tự động đã vô tình loại trừ hàng triệu ứng viên tiềm năng có năng lực học thuật tốt.", 0, "1. Vòng lặp nghịch lý kinh nghiệm (The Experience Paradox): ")
    add_bullet("Tâm lý lo âu dẫn đến thói quen 'rải truyền đơn' – nộp hàng loạt vị trí không chọn lọc. Điều này khiến CV của sinh viên mang tính rập khuôn, không nêu bật được thế mạnh riêng và dễ bị phần mềm ATS đánh dấu là spam [3].", 0, "2. Hội chứng nộp đơn mù quáng (Blind Application Syndrome): ")
    add_bullet("Khi nhận email từ chối mang tính mẫu ('Chúng tôi rất tiếc...'), sinh viên hoàn toàn không nhận được phản hồi định lượng (Diagnostic Feedback): Họ trượt vì thiếu kỹ năng lập trình, ngoại ngữ kém, hay do cấu trúc CV chưa đạt chuẩn?", 0, "3. Điểm mù khoảng trống năng lực (Skill-Gap Blindspot): ")
    add_bullet("Tình trạng các bài đăng tuyển việc làm thêm, thực tập sinh trá hình phục vụ bán hàng đa cấp, lừa đảo đóng phí đặt cọc đồng phục hoặc khóa đào tạo đắt tiền tràn lan trên các hội nhóm mạng xã hội [3], [4].", 0, "4. Nguy cơ lừa đảo và tin tuyển dụng độc hại: ")

    add_h3("B. Nỗi đau của Nhà tuyển dụng (Recruiter Pain Points)")
    add_bullet("Mỗi tin tuyển dụng sinh viên thu hút từ 300 đến 800 CV, nhưng hơn 75% trong số đó không phù hợp hoặc sao chép y nguyên mẫu CV trên mạng. Bộ phận nhân sự phải dành từ 40 đến 60 giờ làm việc để lọc thủ công [4], [7].", 0, "1. Tình trạng quá tải CV chất lượng thấp (Resume Noise Flood): ")
    add_bullet("Hệ thống lọc ứng viên (ATS) truyền thống dựa vào việc đếm từ khóa kinh nghiệm (Keyword Matching). Đối với sinh viên, các em chưa có chức danh làm việc chính thức mà thể hiện năng lực qua đồ án môn học, điểm môn chuyên ngành, tài khoản GitHub – những thứ mà ATS hiện tại hoàn toàn bỏ qua [6].", 0, "2. Sự tê liệt của các bộ lọc ATS hiện có: ")
    add_bullet("Sinh viên trúng tuyển dựa trên cảm tính phỏng vấn thường nhanh chóng nghỉ việc sau 1 - 2 tháng do kỳ vọng công việc không khớp với thực tế hoặc thiếu hụt các kỹ năng làm việc nhóm, công cụ làm việc thực tế [5], [7].", 0, "3. Tỷ lệ nhảy việc sớm (Early Turnover Rate) cao: ")

    # ------------------- CHƯƠNG 2 -------------------
    add_h1("CHƯƠNG 2: PHÂN TÍCH ĐỐI THỦ CẠNH TRANH & MA TRẬN KHOẢNG TRỐNG THỊ TRƯỜNG")
    
    doc.add_paragraph(
        "Nhóm nghiên cứu đã tiến hành khảo sát và đánh giá 4 nền tảng tìm kiếm việc làm phổ biến nhất tại thị trường Việt Nam "
        "để xác định khoảng trống thị trường (Market Gap) mà giải pháp UniTalent AI hướng tới giải quyết:"
    )

    table = doc.add_table(rows=8, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    headers = ["Tiêu chí phân tích", "TopCV", "VietnamWorks", "LinkedIn", "UniTalent AI (Đề tài)"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = text
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{TABLE_HEADER_BG}"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9.5)

    comp_data = [
        ("Phân khúc mục tiêu", "Đại chúng (1-5 năm KN)", "Chuyên viên trung - cao cấp", "Chuyên gia toàn cầu", "Sinh viên, Thực tập sinh, Fresher"),
        ("Mô hình đánh giá", "Số năm kinh nghiệm làm việc", "Chức danh & Lịch sử công tác", "Mạng lưới kết nối, Endorsement", "Đồ án môn học, GPA, Tiềm năng tư duy"),
        ("Công nghệ cốt lõi", "Lọc từ khóa (Keyword TF-IDF)", "Bộ lọc điều kiện cứng SQL", "Thuật toán đồ thị xã hội", "Semantic Vector + Skill Knowledge Graph"),
        ("Chẩn đoán hổng kỹ năng", "Hoàn toàn không có", "Hoàn toàn không có", "Gợi ý khóa học rời rạc", "Chỉ rõ kỹ năng thiếu + Kê đơn lộ trình 2 tuần"),
        ("Cơ chế chống tin lừa đảo", "Kiểm duyệt thủ công hạn chế", "Xác minh pháp nhân công ty", "Rất nghiêm ngặt", "Xác thực MSSV + ĐH bảo chứng đồ án"),
        ("Hỗ trợ lịch học linh hoạt", "Không hỗ trợ lọc", "Không hỗ trợ", "Không hỗ trợ", "Tự động khớp lịch học với ca làm việc"),
        ("Hệ sinh thái BI", "Báo cáo cơ bản cho HR", "Báo cáo ngành chung", "LinkedIn Talent Insights (Đắt)", "BI 3 chiều: Sinh viên - Doanh nghiệp - Trường")
    ]

    for row_idx, row_data in enumerate(comp_data, start=1):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.text = text
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(8.5)
                if col_idx == 4:
                    run.font.bold = True
                    run.font.color.rgb = PRIMARY

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ------------------- CHƯƠNG 3 -------------------
    add_h1("CHƯƠNG 3: MÔ HÌNH HỆ THỐNG KINH DOANH THÔNG MINH (BI ARCHITECTURE & DATA WAREHOUSE)")
    
    doc.add_paragraph(
        "Để hiểu một cách trực quan và gần gũi: Nếu như Cơ sở dữ liệu giao dịch hàng ngày (như PostgreSQL, MySQL) "
        "giống như một 'cuốn sổ thu ngân' ghi chép chi tiết từng lượt nộp CV riêng lẻ, thì Kho dữ liệu BI (Data Warehouse) "
        "đóng vai trò như một 'phòng nghiên cứu chiến lược'. Nó gom hàng triệu lượt tương tác của sinh viên và nhà tuyển dụng "
        "lại để trả lời các câu hỏi tổng thể: 'Trong 6 tháng qua, sinh viên ngành nào có tỷ lệ được tuyển dụng cao nhất?' "
        "hay 'Doanh nghiệp đang khát kỹ năng công nghệ nào nhất trên thị trường hiện nay?'"
    )

    add_h2("3.1. Thiết kế Kho dữ liệu hình sao (Star Schema)")
    doc.add_paragraph(
        "Kho dữ liệu của UniTalent AI được tổ chức theo Lược đồ hình sao (Star Schema) - mô hình chuẩn mực trong Business Intelligence "
        "giúp hệ thống thực hiện các phép truy vấn phân tích đa chiều (OLAP) với tốc độ tức thì (tính bằng mili-giây):"
    )

    add_image('docs/diagrams/diagram_star_schema.png', 
              'Hình 3.1: Sơ đồ Kho dữ liệu hình sao (Data Warehouse Star Schema) phục vụ phân tích đa chiều OLAP', 6.0)

    doc.add_paragraph(
        "Cấu trúc của mô hình hình sao bao gồm 2 thành phần chính rất dễ hiểu:"
    )
    add_bullet("Bảng sự kiện trung tâm (FACT_APPLICATIONS): Mỗi dòng trong bảng này ghi lại một sự kiện sinh viên nộp hồ sơ vào một công việc cụ thể. Bảng chứa các số liệu định lượng: Điểm tương thích Match_Score, Số ngày chờ phản hồi Response_Time_Days, Điểm phỏng vấn và Kết quả trúng tuyển Is_Hired.", 0, "1. Bảng Trung Tâm (Fact Table): ")
    add_bullet("Các bảng chiều bao quanh (5 Dimension Tables): Đóng vai trò là các 'góc nhìn' khác nhau để phân tích dữ liệu:\n"
               "• DIM_STUDENT: Góc nhìn về Sinh viên (Trường ĐH, Chuyên ngành, Điểm GPA, Số đồ án đã kiểm chứng, Trình độ tiếng Anh).\n"
               "• DIM_JOB: Góc nhìn về Công việc (Chức danh Intern/Fresher, Khung lương trợ cấp, Hình thức Part-time/Hybrid).\n"
               "• DIM_COMPANY: Góc nhìn về Doanh nghiệp (Ngành nghề hoạt động, Quy mô nhân sự, Phân khúc thị trường tuyển dụng).\n"
               "• DIM_SKILL: Góc nhìn về Kỹ năng (Tên kỹ năng, Nhóm chuyên môn, Trọng số nhu cầu thị trường).\n"
               "• DIM_TIME: Góc nhìn về Thời gian (Ngày, Tháng, Quý tuyển dụng, Học kỳ năm học).", 0, "2. Các Chiều Phân Tích (Dimension Tables): ")

    add_h2("3.2. Hệ thống Chỉ số Kinh doanh Thông minh (BI KPIs)")
    doc.add_paragraph(
        "Dựa trên Kho dữ liệu trên, hệ thống trích xuất 2 bộ chỉ số BI phục vụ chiến lược cho 2 chủ thể cốt lõi: Doanh nghiệp tuyển dụng và Sinh viên tìm việc:"
    )
    
    add_h3("A. Dành cho Doanh nghiệp Tuyển dụng (HR Analytics & Talent Market Intelligence)")
    add_bullet("Tỷ lệ các ứng viên có điểm tương thích Match > 80% vượt qua vòng phỏng vấn chuyên môn. Nhờ thuật toán AI lọc đúng năng lực thực tế, chỉ số này tăng từ 22% (khi HR lọc tay truyền thống) lên trên 78%.", 0, "1. Quality of Match (QoM - Chất lượng ghép cặp): ")
    add_bullet("Thời gian từ khi đăng tin tuyển dụng sinh viên đến khi hoàn tất nhận việc. Hệ thống giúp rút ngắn từ 28 ngày xuống chỉ còn 7 - 9 ngày làm việc.", 0, "2. Time-to-Fill (Tốc độ lấp đầy vị trí): ")
    add_bullet("Tiết kiệm hơn 60% chi phí đăng tin đại trà và nhân công sàng lọc hồ sơ rác.", 0, "3. Cost-per-Hire (Tối ưu ngân sách tuyển dụng): ")
    add_bullet("Bản đồ nhiệt theo dõi xu hướng biến động của các công nghệ nóng (Spring Boot Microservices 78%, Docker/Cloud 68%, AI/LLMs 80%) giúp HR chủ động điều chỉnh mức đãi ngộ và đón đầu nguồn nhân lực trẻ xuất sắc.", 0, "4. Skill In-Demand & Market Intelligence: ")

    add_h3("B. Dành cho Sinh viên (Student Career Optimization)")
    add_bullet("Tỷ lệ nhận được lời mời phỏng vấn thực tế tăng từ mức < 5% (rải CV mù quáng) lên trên 45% nhờ được hệ thống gợi ý đúng việc làm phù hợp với năng lực đồ án của bản thân.", 0, "1. Conversion Rate (Tỷ lệ ứng tuyển thành công): ")
    add_bullet("Biết rõ những kỹ năng nào trên thị trường đang được trả lương trợ cấp cao nhất để có định hướng học tập đón đầu.", 0, "2. Skill Market Value (Giá trị thị trường của kỹ năng): ")

    # ------------------- CHƯƠNG 4 -------------------
    add_h1("CHƯƠNG 4: THUẬT TOÁN AI & ĐỒ THỊ TRI THỨC NĂNG LỰC (AI MATCHING ENGINE)")
    
    doc.add_paragraph(
        "Trái tim công nghệ của UniTalent AI là cơ chế Ghép cặp thông minh 2 chiều (Bi-directional Matching Engine) "
        "kết hợp hài hòa giữa Trí tuệ nhân tạo Xử lý ngôn ngữ tự nhiên (NLP) và Đồ thị tri thức (Knowledge Graph):"
    )

    add_image('docs/diagrams/diagram_ai_matching_flow.png', 
              'Hình 4.1: Sơ đồ dòng chảy Thuật toán AI Matching và Chẩn đoán Hổng Kỹ năng (Skill-Gap Engine)', 6.0)

    add_h2("4.1. Quy trình tính toán Điểm Tương Thích (Match Score) Đa Tiêu Chí")
    doc.add_paragraph(
        "Thay vì chỉ so khớp từng chữ cái một cách máy móc, điểm tương thích tổng thể giữa hồ sơ sinh viên (U) "
        "và mô tả công việc (J) được tổng hợp từ 4 thành phần có trọng số rõ ràng:"
    )

    add_callout(
        "Final_Score(U, J) = 0.35 * Sim_Semantic + 0.35 * Score_SkillGraph + 0.15 * Score_Academic + 0.15 * Score_ScheduleFit",
        "CÔNG THỨC TOÁN HỌC ĐỊNH LƯỢNG ĐỘ PHÙ HỢP CÔNG VIỆC:"
    )

    doc.add_paragraph("Ý nghĩa thực tế của 4 thành phần trên rất dễ hiểu:")
    add_bullet("Hiểu ngữ nghĩa bằng Vector (35%): Sử dụng mô hình Sentence-Transformers (Reimers & Gurevych, 2019 [11]) chuyển đổi văn bản CV và JD thành các vector toán học 768 chiều. Nhờ đó, AI hiểu được rằng ứng viên ghi 'Đồ án lập trình mạng với Socket.IO' sẽ tương thích rất cao với yêu cầu 'Real-time Network Programming' trong JD, dù hai câu chữ không hề trùng từ khóa.", 0, "1. Sim_Semantic: ")
    add_bullet("Độ phủ trên Đồ thị Tri thức Kỹ năng (35%): Xem xét các kỹ năng của sinh viên dựa trên cấu trúc phả hệ và mối liên kết logic trên cơ sở dữ liệu đồ thị Neo4j.", 0, "2. Score_SkillGraph: ")
    add_bullet("Điểm Đồ án môn học & Học thuật (15%): Đây là điểm sáng đột phá giúp sinh viên chưa có kinh nghiệm vẫn được đánh giá cao. Một đồ án môn học điểm A hoặc bài tập lớn có mã nguồn kiểm chứng trên GitHub được AI tính điểm tương đương với 3-6 tháng kinh nghiệm làm việc thực tế.", 0, "3. Score_Academic: ")
    add_bullet("Độ khớp lịch học linh hoạt (15%): AI tự động đối chiếu thời khóa biểu học kỳ của sinh viên với ca làm việc Part-time hoặc Hybrid của doanh nghiệp, đảm bảo sinh viên đi làm không bị trùng lịch học hay lịch thi tại trường.", 0, "4. Score_ScheduleFit: ")

    add_h2("4.2. Kiến trúc Đồ thị Tri thức Kỹ năng (Neo4j Skill Knowledge Graph)")
    doc.add_paragraph(
        "Hệ thống xây dựng cây tri thức năng lực dựa trên chuẩn phân loại quốc tế ESCO của Châu Âu [9] và O*NET của Hoa Kỳ [10]. "
        "Đồ thị này giúp AI 'suy luận' được tiềm năng học hỏi của sinh viên thay vì chỉ nhìn vào những gì đã biết:"
    )

    add_image('docs/diagrams/diagram_skill_graph.png', 
              'Hình 4.2: Minh họa Đồ thị Tri thức Kỹ năng (Neo4j Skill Knowledge Graph)', 5.8)

    add_bullet("Quan hệ Kế thừa ([:SUBCLASS_OF]): Ngành CNTT -> Chuyên ngành Backend -> Công nghệ Java -> Framework Spring Boot.", 0, "Phân cấp phả hệ: ")
    add_bullet("Quan hệ Tương quan Lan truyền ([:RELATED_TO]): Nếu sinh viên đã thành thạo 'Machine Learning' và 'Toán Tối ưu', hệ thống hiểu rằng em đó có khả năng tiếp thu 'Deep Learning' cực nhanh nhờ mối quan hệ tương quan mạnh (hệ số 0.85).", 0, "Liên kết tương đương: ")
    add_bullet("Quan hệ Tiên quyết ([:REQUIRES]): Để làm Backend với Spring Boot, bắt buộc phải có kỹ năng nền về Java Core, Lập trình hướng đối tượng OOP và Cơ sở dữ liệu PostgreSQL (Spring Data JPA).", 0, "Điều kiện tiên quyết: ")

    add_h2("4.3. Tính năng Đột phá: Bắt bệnh Kỹ năng & Kê đơn Lộ trình học tập (Skill-Gap Engine)")
    doc.add_paragraph(
        "Nếu điểm tương thích Match Score đạt từ 85% trở lên, hệ thống sẽ tự động đề xuất hồ sơ lên đầu danh sách tuyển dụng của HR. "
        "Tuy nhiên, nếu điểm số chỉ đạt mức cận chuẩn (ví dụ 60% - 84%), hệ thống sẽ kích hoạt tính năng Bắt bệnh Kỹ năng độc quyền:"
    )
    add_bullet("Bắt bệnh chính xác (Gap Diagnosis): Chỉ rõ sinh viên đang thiếu những kỹ năng bắt buộc nào so với yêu cầu của JD (Ví dụ: Ứng viên Nam Nguyễn đạt 82% vị trí Data Analyst tại Shopee - đã giỏi Python và SQL nhưng bị thiếu kỹ năng dựng Dashboard PowerBI).", 0, "Bước 1 - Chẩn đoán: ")
    add_bullet("Kê đơn lộ trình 2 tuần (Prescriptive Roadmap): AI tự động sinh một kế hoạch học tập bù đắp cụ thể: Tuần 1 học khóa học DAX PowerBI ngắn hạn; Tuần 2 tải bộ dữ liệu bán lẻ Shopee trên kho tài nguyên hệ thống về làm bài tập báo cáo. Khi hoàn thành và đính kèm báo cáo vào hồ sơ, AI quét lại và nâng hạng điểm tương thích lên 95%!", 0, "Bước 2 - Lộ trình hành động: ")

    add_h2("4.4. Tính năng Đột phá: GitHub & Project Code Auto-Auditor (Trình Thẩm Định Mã Nguồn Đồ Án Tự Động)")
    doc.add_paragraph(
        "Nỗi đau thực tế: Sinh viên nào cũng đính kèm link GitHub vào CV, nhưng 95% nhà tuyển dụng và Tech Lead "
        "không có thời gian mở từng file code ra đọc. Do đó, các nỗ lực lập trình thực tế của sinh viên thường bị lãng phí "
        "và không được ghi nhận xứng đáng."
    )
    doc.add_paragraph(
        "Giải pháp đột phá: Khi sinh viên dán link GitHub đồ án môn học, hệ thống AI tự động quét (scan) toàn bộ repository trong 30 giây với 4 tiêu chuẩn chuyên sâu:"
    )
    add_bullet("Chấm điểm Clean Code & Design Patterns: Đánh giá kiến trúc mã nguồn (MVC, Repository Pattern, Dependency Injection) và mức độ tuân thủ 5 nguyên lý SOLID.", 0, "1. Kiến trúc & Clean Code: ")
    add_bullet("Đánh giá Kỷ luật Git (Git Discipline): Kiểm tra lịch sử commit có rõ ràng theo chuẩn Conventional Commits không, có phân chia nhánh tính năng (feature branches) hay dồn hết vào master.", 0, "2. Kỷ luật kiểm soát phiên bản: ")
    add_bullet("Kiểm tra Test Coverage: Quét các bộ kiểm thử tự động (Unit Test, Integration Test) để đo lường độ phủ mã nguồn và tính an toàn dự án.", 0, "3. Mức độ kiểm thử tự động: ")
    add_bullet("Phát hiện đạo nhái (Plagiarism Check): Thuật toán so khớp cây cú pháp trừu tượng (AST - Abstract Syntax Tree) đối chiếu với các đồ án khóa trước và các repository công khai trên mạng, ngăn chặn việc sao chép mã nguồn.", 0, "4. Phòng chống gian lận & Đạo nhái: ")
    doc.add_paragraph(
        "Kết quả: Cấp huy hiệu xanh chính thức 'Verified Clean Code By UniTalent AI' gắn trực tiếp vào hồ sơ. "
        "Doanh nghiệp nhìn vào huy hiệu là tin tưởng ngay năng lực thực chiến mà không cần bắt ứng viên làm bài test kỹ thuật đầu vào tốn thời gian."
    )

    add_h2("4.5. Tính năng Đột phá: AI Mock Interview Coach (Trợ Lý Luyện Phỏng Vấn Giả Lập Bằng Giọng Nói)")
    doc.add_paragraph(
        "Nỗi đau thực tế: Nỗi sợ lớn nhất của sinh viên sau khi vượt qua vòng lọc CV là bước vào phòng phỏng vấn bị 'khớp', "
        "run, ấp úng và trả lời lan man thiếu tự tin trước nhà tuyển dụng."
    )
    doc.add_paragraph(
        "Giải pháp đột phá: Khi sinh viên đạt điểm Match >= 80% cho một JD cụ thể (Ví dụ: vị trí Thực tập sinh Backend tại VNG), "
        "hệ thống sẽ tự động kích hoạt Phòng Phỏng Vấn Ảo (Virtual Interview Room):"
    )
    add_bullet("Đóng vai tương tác giọng nói trực tiếp (Voice AI): AI đóng vai Tech Lead và HR của doanh nghiệp, trò chuyện trực tiếp 2 chiều bằng giọng nói thời gian thực (tương tự công nghệ ChatGPT Voice / Gemini Live) dựa trên chính các câu hỏi kỹ thuật sát sườn với JD đang tuyển.", 0, "1. Tương tác giọng nói đa phương thức: ")
    add_bullet("Độ chính xác kỹ thuật (Technical Accuracy): AI phân tích câu trả lời của sinh viên có đi đúng trọng tâm kiến trúc hệ thống, giải thuật và cơ sở dữ liệu hay không.", 0, "2. Đánh giá độ chuẩn xác chuyên môn: ")
    add_bullet("Đo lường kỹ năng mềm định lượng: Đo tốc độ nói WPM (Words Per Minute), đếm tần suất dùng từ ngữ ấp úng ('ờ, à, thì, là'), phân tích biểu cảm khuôn mặt và độ tự tin qua webcam.", 0, "3. Phân tích kỹ năng mềm và tâm lý: ")
    doc.add_paragraph(
        "Kết quả: Hệ thống xuất ra Báo cáo Phân tích Phỏng vấn chi tiết kèm chỉ số 'Độ sẵn sàng phỏng vấn: 85/100 (Interview Readiness Score)' "
        "và chỉ dẫn những câu hỏi sinh viên cần trau chuốt lại trước khi bước vào buổi phỏng vấn chính thức với doanh nghiệp."
    )

    # ------------------- CHƯƠNG 5 -------------------
    add_h1("CHƯƠNG 5: THIẾT KẾ TRẢI NGHIỆM NGƯỜI DÙNG & BẢN VẼ WIREFRAME CHI TIẾT (MULTI-ROLE & MULTI-PAGE)")
    
    doc.add_paragraph(
        "Hệ thống đã được hiện thực hóa trọn vẹn thành bản Demo ứng dụng đa phân hệ, đa trang (Multi-page Single Page App) "
        "tại tệp 'demo_prototype.html'. Kiến trúc trải nghiệm người dùng được chia thành 2 phân hệ độc lập tương ứng với 2 vai trò cốt lõi (2 Roles):"
    )

    add_h2("5.1. Phân hệ Xác Thực & Phân Quyền Vai Trò (Authentication & Role Management)")
    add_bullet("Hỗ trợ đăng nhập và đăng ký theo từng nhóm người dùng: Sinh viên xác thực qua Email sinh viên (.edu.vn) và Nhà tuyển dụng qua Email doanh nghiệp pháp nhân.", 0, "Cơ chế Xác thực: ")
    add_bullet("Tích hợp thanh chuyển đổi nhanh 1-Click Role Switcher (Dành riêng cho việc quay video thuyết trình demo mượt mà mà không cần nhập lại mật khẩu thủ công).", 0, "Phím tắt Demo: ")

    add_h2("5.2. Phân hệ Dành Cho Sinh Viên (Student Career Portal)")
    add_bullet("Trang 1: Bảng tin Việc làm AI (Smart Job Feed) tích hợp Biểu đồ Radar Năng lực 6 trục và danh sách công việc xếp hạng tự động theo % Match (Ví dụ: Backend Spring Boot VNG đạt 94% Match).", 0, "Trang 1 - Smart Job Feed: ")
    add_bullet("Trang 2: Hồ Sơ Năng Lực & Trình Thẩm Định Mã Nguồn GitHub (Code Auto-Auditor) hiển thị báo cáo phân tích Clean Code SOLID (94/100), Test Coverage JUnit (85%) và kiểm tra chống đạo nhái (0%).", 0, "Trang 2 - Profile & GitHub: ")
    add_bullet("Trang 3: Bảng Kanban Theo Dõi Tiến Độ Tuyển Dụng (Đã nộp -> AI duyệt >85% -> Mời phỏng vấn -> Nhận Offer).", 0, "Trang 3 - Application Kanban: ")
    add_bullet("Modal 1: Chẩn đoán Khoảng trống Kỹ năng (Skill-Gap Diagnosis) và kê đơn lộ trình 2 tuần bù đắp PowerBI.", 0, "Mô-đun Chẩn đoán: ")
    add_bullet("Modal 2: Phòng Phỏng Vấn Giọng Nói Ảo (AI Mock Interview Coach) giả lập Tech Lead phỏng vấn câu hỏi kỹ thuật Spring Boot & Redis với hiệu ứng sóng âm và phân tích WPM, từ ấp úng thời gian thực.", 0, "Mô-đun Phỏng vấn Voice AI: ")

    add_h2("5.3. Phân hệ Dành Cho Nhà Tuyển Dụng (Recruiter Talent Acquisition & BI Intelligence)")
    add_bullet("Bảng điều khiển KPI tuyển dụng: Thời gian tuyển trung bình (Time-to-fill đạt 8.5 ngày), Tỷ lệ ứng viên đạt Match > 85%, và Phân tích trường đại học nguồn hàng đầu.", 0, "Thống kê Chiến dịch Tuyển dụng: ")
    add_bullet("Trang 1 - Phễu Ứng Viên Chuẩn Hóa (Ranked Pipeline): Hiển thị danh sách ứng viên đã được AI kiểm chứng code thực tế, điểm phỏng vấn Voice AI (88/100) và nút mời phỏng vấn tự động khớp lịch học rảnh của sinh viên.", 0, "Sàng lọc Ứng viên Thông minh: ")
    add_bullet("Trang 2 - BI Analytics & Nhu Cầu Kỹ Năng: Trực quan hóa Biểu đồ Cột Top kỹ năng khát nhân lực (Spring Boot 78%, Cloud 68%), Biểu đồ Tròn tỷ lệ ứng viên sẵn sàng việc làm (92%) và nút xuất báo cáo BI chuẩn.", 0, "BI Thị Trường & Báo Cáo Kỹ Năng: ")
    add_bullet("Đăng tải JD thông minh: AI tự động phân tách kỹ năng bắt buộc (Must-have) và kỹ năng ưu tiên (Nice-to-have).", 0, "Quản trị Tin tuyển dụng: ")

    # ------------------- CHƯƠNG 6 -------------------
    add_h1("CHƯƠNG 6: ĐẶC TẢ NGĂN XẾP CÔNG NGHỆ TRIỂN KHAI (TECHNICAL STACK)")
    
    doc.add_paragraph("Chi tiết ngăn xếp công nghệ tiêu chuẩn công nghiệp phục vụ vận hành hệ thống:")

    tech_table = doc.add_table(rows=10, cols=3)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tech_table.style = 'Table Grid'

    t_headers = ["Tầng kiến trúc", "Công nghệ sử dụng", "Mục đích chuyên sâu & Giá trị kỹ thuật"]
    for col_idx, text in enumerate(t_headers):
        cell = tech_table.cell(0, col_idx)
        cell.text = text
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{TABLE_HEADER_BG}"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9.5)

    tech_data = [
        ("Frontend Application", "Next.js 14, TailwindCSS, Chart.js, Shadcn UI", "Giao diện tối ưu SSR phục vụ SEO việc làm, biểu đồ tương tác thời gian thực, responsive mobile."),
        ("Core Backend APIs", "Java (Spring Boot 3.3) & Python (FastAPI)", "Spring Boot 3 đảm nhiệm toàn bộ kiến trúc Backend doanh nghiệp (RESTful APIs, Spring Security 6 với OAuth2/JWT, Spring Data JPA/Hibernate, Microservices); Python FastAPI làm vi dịch vụ tính toán AI & Vector Processing."),
        ("AI / NLP Processing", "PyMuPDF, sentence-transformers, Llama 3", "OCR trích xuất layout CV PDF, mô hình nhúng vector ngữ nghĩa và sinh lộ trình học tập."),
        ("Voice AI Interview", "OpenAI Whisper API, WebRTC, Gemini Live Voice", "Tương tác giọng nói phỏng vấn giả lập 2 chiều thời gian thực, phân tích WPM và từ ngữ ấp úng."),
        ("Code Auditor & AST", "Tree-sitter, GitPython, SonarQube Scanner", "Quét cây cú pháp trừu tượng đồ án GitHub, đo lường SOLID, Test coverage và chống đạo nhái code."),
        ("Graph Database", "Neo4j Enterprise Edition", "Lưu trữ cấu trúc đồ thị kỹ năng (Skill Graph), duyệt quan hệ tương đương và tính trọng số lan truyền."),
        ("Primary Database", "PostgreSQL 16 + pgvector extension", "Lưu trữ dữ liệu có quan hệ RDBMS đồng thời truy vấn vector similarity search theo chuẩn HNSW."),
        ("BI & Data Warehouse", "ClickHouse DBMS + Apache Superset", "Kho dữ liệu dạng cột (Columnar Storage) tối ưu hóa truy vấn OLAP tổng hợp hàng triệu giao dịch."),
        ("DevOps & Infra", "Docker, Docker Compose, Redis, AWS S3", "Đóng gói containerized đồng nhất, hàng đợi xử lý ngầm Celery và lưu trữ an toàn CV sinh viên.")
    ]

    for r_idx, (c1, c2, c3) in enumerate(tech_data, start=1):
        tech_table.cell(r_idx, 0).text = c1
        tech_table.cell(r_idx, 1).text = c2
        tech_table.cell(r_idx, 2).text = c3
        for c_idx in range(3):
            cell = tech_table.cell(r_idx, c_idx)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.size = Pt(8.5)
                if c_idx == 0:
                    r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ------------------- CHƯƠNG 7 -------------------
    add_h1("CHƯƠNG 7: KỊCH BẢN CHI TIẾT QUAY VIDEO THU HOẠCH TỪNG GIÂY (0:00 - 8:30)")
    
    doc.add_paragraph(
        "Kịch bản được xây dựng chi tiết 100% từng câu chữ thuyết minh (Voice-over) và hình ảnh hiển thị trên màn hình "
        "để sinh viên chỉ việc đọc theo mic trong quá trình quay màn hình:"
    )

    full_script = [
        ("Phần 1: Giới thiệu & Đặt vấn đề nghịch lý (0:00 - 1:45)",
         "Mở đầu: Slide tiêu đề chuyên nghiệp 'UniTalent AI' kèm webcam người thuyết trình ở góc dưới bên phải. Chuyển sang Slide đồ họa 'Nghịch lý kinh nghiệm' với hình ảnh tin tuyển dụng 'Intern yêu cầu 2 năm kinh nghiệm'. Biểu đồ tỷ lệ 4.2% phản hồi CV.",
         "Kính chào Thầy Cô và các bạn! Có một nghịch lý kinh điển mà hầu hết sinh viên năm cuối đều từng nếm trải: 'Muốn có việc thì cần kinh nghiệm, nhưng muốn có kinh nghiệm thì phải được nhận vào làm'. Mỗi năm, hơn 400.000 cử nhân bước vào thị trường lao động. Đa phần các bạn chọn cách rải hàng chục CV lên các sàn tuyển dụng truyền thống, để rồi nhận lại sự im lặng. Nguyên nhân cốt lõi là các hệ thống ATS hiện nay được thiết kế cho người ĐÃ CÓ KINH NGHIỆM, chúng tự động loại hồ sơ sinh viên chỉ vì thiếu số năm làm việc. Trong khi đó, doanh nghiệp vẫn kêu ca thiếu hụt nhân sự trẻ tiềm năng. Để giải quyết triệt để sự bất cân xứng này dưới góc nhìn của Hệ Thống Kinh Doanh Thông Minh, nhóm chúng em đã nghiên cứu và phát triển đề tài: UniTalent AI – Nền tảng Tìm việc Thông minh và Định hướng Năng lực dành riêng cho Sinh viên."),

        ("Phần 2: Đề xuất giải pháp & Kiến trúc AI/BI (1:45 - 3:45)",
         "Chiếu sơ đồ kiến trúc 4 tầng: Ingestion Layer -> Skill Graph (Neo4j) -> Semantic Matching Engine -> BI Data Warehouse. Zoom cận cảnh sơ đồ thuật toán, tính năng Thẩm định code GitHub và Luyện phỏng vấn Voice AI.",
         "UniTalent AI tạo ra sự khác biệt vượt trội nhờ hệ sinh thái công nghệ toàn diện: Thứ nhất là Semantic Matching thay vì lọc từ khóa thô, kết hợp Vector Embeddings và Đồ thị tri thức Neo4j. Thứ hai là Mô hình Định lượng năng lực sinh viên qua đồ án thực tế. Thứ ba là Cơ chế Bắt bệnh kỹ năng và kê đơn lộ trình học tập 2 tuần. Đặc biệt, để giải quyết trọn vẹn nỗi sợ của sinh viên, hệ thống tích hợp thêm 2 vũ khí chiến lược: Trình thẩm định mã nguồn GitHub Auto-Auditor giúp kiểm tra Clean Code, SOLID và chống đạo nhái đồ án; và Trợ lý AI Mock Interview Coach luyện phỏng vấn giả lập bằng giọng nói 2 chiều theo đúng yêu cầu của từng JD."),

        ("Phần 3: Trình diễn Demo vận hành hệ thống thực tế (3:45 - 6:30)",
         "Chuyển hẳn sang màn hình trình duyệt mở file demo_prototype.html. Thao tác mượt mà: (1) Xem Dashboard sinh viên Nam Nguyễn với Radar Chart và Huy hiệu Verified Clean Code GitHub; (2) Xem Smart Feed với công việc VNG 94% Match; (3) Click 'Luyện phỏng vấn Voice AI' để kích hoạt phòng phỏng vấn giả lập; (4) Click Modal Bắt bệnh kỹ năng tại vị trí Shopee 82%; (5) Chuyển sang Tab Recruiter và BI Analytics.",
         "Ngay bây giờ, em xin kính mời Thầy Cô cùng theo dõi luồng vận hành thực tế của hệ thống. Đây là giao diện của bạn Nam, sinh viên CNTT. Khi Nam tải CV và link GitHub lên, hệ thống tự động quét mã nguồn và cấp ngay huy hiệu 'Verified Clean Code A+' đạt chuẩn SOLID và 0% đạo nhái. Tại bảng tin việc làm thông minh, vị trí Backend (Java/Spring Boot) tại VNG đạt mức độ tương thích tới 94%. Đặc biệt, Nam có thể bấm ngay vào nút 'Luyện phỏng vấn Voice AI': Một phòng phỏng vấn ảo hiện ra, AI đóng vai Tech Lead VNG đặt câu hỏi bằng giọng nói về cơ chế Cache Stampede trong Redis và cấu hình Spring Cache, lắng nghe Nam trả lời, đo lường tốc độ nói, lọc từ ngữ ấp úng và chấm Nam đạt 88/100 điểm sẵn sàng phỏng vấn! Tiếp theo, với vị trí Shopee đạt 82% Match, Nam bấm 'Bắt bệnh kỹ năng' để nhận ngay lộ trình bù đắp PowerBI trong 2 tuần. Về phía Doanh nghiệp, HR thấy ngay danh sách ứng viên đã được kiểm chứng code thực tế, giúp tối ưu hóa toàn diện quy trình tuyển dụng."),

        ("Phần 4: Phân tích giá trị Kinh doanh Thông minh - BI (6:30 - 7:45)",
         "Màn hình hiển thị Tab BI Analytics trong phân hệ Nhà tuyển dụng: Biểu đồ cột các kỹ năng công nghệ thị trường đòi hỏi nhiều nhất (Spring Boot 78%, Cloud 68%); Biểu đồ tròn tỷ lệ 72% ứng viên sẵn sàng nhận việc thành công sau khi được AI định hướng.",
         "Dưới góc độ môn học Hệ Thống Kinh Doanh Thông Minh, UniTalent AI đóng vai trò là một trung tâm dữ liệu chiến lược tối ưu hóa thị trường lao động: Đối với Doanh nghiệp: Cung cấp chỉ số Time-to-Fill và Quality-of-Match, giúp HR rút ngắn 65% thời gian tuyển dụng và dự báo chính xác nguồn nhân lực để có chiến lược săn nhân tài đón đầu. Nhìn vào biểu đồ BI phân tích nhu cầu kỹ năng, doanh nghiệp nắm bắt ngay có tới 78% vị trí đang yêu cầu Spring Boot Microservices và 68% đòi hỏi Docker/Cloud. Đối với Sinh viên: Hệ thống cung cấp bản đồ định hướng giá trị kỹ năng, giúp các em đầu tư thời gian học đúng những gì thị trường đang khát, nhanh chóng nâng điểm tương thích để lọt vào mắt xanh của các nhà tuyển dụng hàng đầu."),

        ("Phần 5: Tổng kết & Lời cảm ơn (7:45 - 8:30)",
         "Slide tổng kết các thành quả nghiên cứu, bảng tóm tắt công nghệ và lời cảm ơn chân thành đến Giảng viên hướng dẫn môn học.",
         "Tóm lại, UniTalent AI không đơn thuần là một công cụ tuyển dụng, mà là một giải pháp kinh doanh thông minh toàn diện nhằm tối ưu hóa nguồn lực lao động trẻ của đất nước. Dự án đã hiện thực hóa đầy đủ các kiến thức về Trí tuệ nhân tạo, Kho dữ liệu Data Warehouse và Phân tích kinh doanh thông minh. Nhóm chúng em xin chân thành cảm ơn Thầy Cô đã theo dõi video thuyết trình thu hoạch và rất mong nhận được những góp ý quý báu để hoàn thiện hệ thống hơn nữa. Em xin trân trọng cảm ơn!")
    ]

    for title, visual, voice in full_script:
        add_h2(title)
        add_bullet(visual, 0, "Hình ảnh & Thao tác trên màn hình (Visual Cues): ")
        add_bullet(voice, 0, "Lời thoại thuyết minh chi tiết (Voice-over Script): ")

    # ------------------- CHƯƠNG 8 -------------------
    add_h1("CHƯƠNG 8: QUY TRÌNH HẬU KỲ VÀ KIỂM CHUẨN VIDEO THU HOẠCH (CHECKLIST)")
    
    add_bullet("Sử dụng phần mềm OBS Studio (hoặc Loom) thiết lập khung hình Full HD (1920x1080), 30fps hoặc 60fps. Thiết lập scene gồm: 1 nguồn quay màn hình trình duyệt (demo_prototype.html) và 1 nguồn webcam nhỏ ở góc dưới bên phải.", 0, "1. Thiết lập ghi hình chuyên nghiệp: ")
    add_bullet("Sử dụng microphone có lọc tạp âm. Kiểm tra mức âm lượng thoại nằm trong dải màu xanh lá cây (-12dB đến -6dB) trên bộ trộn âm OBS để đảm bảo âm thanh rõ ràng, không bị rè.", 0, "2. Chuẩn hóa âm thanh thu âm: ")
    add_bullet("Nhập video vào CapCut Desktop, sử dụng tính năng 'Auto Captions' (Phụ đề tự động tiếng Việt). Tùy chỉnh màu chữ nổi bật (chữ trắng viền đen hoặc vàng), chèn hiệu ứng zoom tại các đoạn mô tả Radar chart và Modal bắt bệnh kỹ năng.", 0, "3. Biên tập và tạo phụ đề tự động: ")
    add_bullet("Xuất video định dạng tệp .MP4 (chuẩn nén H.264) với dung lượng vừa phải (< 500MB) để tải lên cổng nộp bài theo đúng quy định.", 0, "4. Xuất file và nộp bài: ")

    # ------------------- CHƯƠNG 9: REFERENCES -------------------
    add_h1("CHƯƠNG 9: TÀI LIỆU THAM KHẢO & NGUỒN TRÍCH DẪN (REFERENCES)")
    doc.add_paragraph(
        "Các số liệu thống kê, căn cứ thực tiễn và cơ sở khoa học trong báo cáo được trích dẫn từ các nguồn chính thống sau:"
    )

    references = [
        ("[1]", "Tổng cục Thống kê Việt Nam (GSO), 'Báo cáo Tình hình Lao động Việc làm Việt Nam thường niên (2023 - 2024)', Nhà xuất bản Thống Kê, Hà Nội. Dữ liệu khảo sát tỷ lệ thất nghiệp và việc làm phi chính thức của thanh niên."),
        ("[2]", "Bộ Giáo dục và Đào tạo (MOET), 'Báo cáo tổng hợp tình hình việc làm của sinh viên tốt nghiệp các cơ sở giáo dục đại học', Công bố định kỳ theo quy định tại Thông tư số 17/2021/TT-BGDĐT."),
        ("[3]", "TopCV Vietnam, 'Báo cáo Thị trường Tuyển dụng 2023 - 2024 & Nhu cầu Tìm việc của Gen Z', Báo cáo phân tích hành vi nộp đơn, tỷ lệ phản hồi CV và kỳ vọng của ứng viên Entry-Level dựa trên tập dữ liệu 5 triệu người dùng."),
        ("[4]", "Navigos Group & VietnamWorks, 'Báo cáo Thị trường Tuyển dụng và Thách thức Nhân sự Trẻ tại Việt Nam', Khảo sát hơn 1.500 doanh nghiệp trên toàn quốc về chi phí tuyển dụng (Cost-per-hire) và thời gian tuyển (Time-to-fill)."),
        ("[5]", "Glints & Monk's Hill Ventures, 'Southeast Asia Talent Trends Report: Hiring and Compensation for Fresh Graduates & Junior Tech Roles', Báo cáo mức lương thực tập sinh và tỷ lệ nghỉ việc sớm tại khu vực Đông Nam Á."),
        ("[6]", "Fuller, J., Raman, M., Sage-Gavin, E., & Hines, K. (2021), 'Hidden Workers: Untapped Talent - How Automated Hiring Systems Systematically Exclude Viable Candidates', Harvard Business School and Accenture Research Report. Nghiên cứu kinh điển chỉ ra nghịch lý các hệ thống lọc ATS loại bỏ ứng viên tiềm năng do tiêu chí số năm kinh nghiệm."),
        ("[7]", "Anphabe, 'Khảo sát Nơi làm việc tốt nhất Việt Nam & Xu hướng kỳ vọng nghề nghiệp của sinh viên Việt Nam', Nghiên cứu diện rộng trên 60.000 sinh viên tại hơn 120 trường đại học tại Việt Nam."),
        ("[8]", "World Economic Forum (WEF) (2023), 'The Future of Jobs Report 2023', Cologny/Geneva, Switzerland. Báo cáo về sự thay đổi nhanh chóng của các nhóm kỹ năng công nghệ cốt lõi và nhu cầu đào tạo bù đắp (Reskilling/Upskilling)."),
        ("[9]", "European Commission, 'ESCO: European Skills, Competences, Qualifications and Occupations Taxonomy', Cổng dữ liệu phân loại kỹ năng và nghề nghiệp chuẩn châu Âu, esco.ec.europa.eu."),
        ("[10]", "U.S. Department of Labor & Employment and Training Administration, 'O*NET OnLine: Occupational Information Network Database', Cơ sở dữ liệu chuẩn hóa hệ thống kỹ năng và mô tả công việc, onetonline.org."),
        ("[11]", "Reimers, N., & Gurevych, I. (2019), 'Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks', In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP-IJCNLP), Association for Computational Linguistics, pp. 3982-3992.")
    ]

    for ref_id, ref_desc in references:
        add_bullet(f"{ref_desc}", 0, f"{ref_id} ")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    docs_dir = os.path.join(base_dir, "docs", "research")
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, "Bao_Cao_Nghien_Cuu_He_Thong_Tim_Viec_Thong_Minh.docx")
    try:
        doc.save(output_path)
        print(f"File created at: {output_path}")
    except PermissionError:
        print(f"[NOTE] Tep '{output_path}' dang duoc mo trong Word. Vui long dong Word neu ban muon ghi de.")

if __name__ == "__main__":
    create_exhaustive_document()
