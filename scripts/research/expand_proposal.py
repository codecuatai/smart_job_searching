from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parents[2]
DOC_IN = ROOT / "docs" / "research" / "De_Xuat_He_Thong_Tim_Viec_Thong_Minh_Va_Chien_Luoc_Du_Lieu.docx"
DOC_OUT = ROOT / "docs" / "research" / "De_Xuat_He_Thong_Tim_Viec_Thong_Minh_Chi_Tiet.docx"
DIAGRAMS = ROOT / "docs" / "diagrams"
DIAGRAMS.mkdir(exist_ok=True)

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def text_center(draw, xy, text, fnt, fill="#172554"):
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=8, align="center")
    x = (xy[0] - (box[2]-box[0]) / 2)
    y = xy[1] - (box[3]-box[1]) / 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=8, align="center")

def wrap_lines(text, width=28):
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))

def box(draw, rect, title, body, color="#DBEAFE", title_color="#1D4ED8", body_size=28, title_size=31):
    draw.rounded_rectangle(rect, radius=22, fill=color, outline=title_color, width=4)
    x1,y1,x2,y2=rect
    draw.rounded_rectangle((x1,y1,x2,y1+70), radius=22, fill=title_color)
    draw.rectangle((x1,y1+42,x2,y1+70), fill=title_color)
    text_center(draw, ((x1+x2)/2,y1+34), title, font(title_size, True), "white")
    draw.multiline_text((x1+22,y1+92), body, font=font(body_size), fill="#243247", spacing=12)

def arrow(draw, a, b, color="#64748B", width=6):
    draw.line((a,b), fill=color, width=width)
    import math
    ang=math.atan2(b[1]-a[1], b[0]-a[0]); length=22
    pts=[b,(b[0]-length*math.cos(ang-0.48),b[1]-length*math.sin(ang-0.48)),(b[0]-length*math.cos(ang+0.48),b[1]-length*math.sin(ang+0.48))]
    draw.polygon(pts, fill=color)

def diagram_dfd(path):
    W,H=3000,1700
    im=Image.new("RGB",(W,H),"#F8FAFC"); d=ImageDraw.Draw(im)
    text_center(d,(W/2,70),"DFD LEVEL 1 · TỪ NGUỒN DỮ LIỆU ĐẾN KẾT QUẢ TÌM VIỆC",font(47,True),"#0F172A")
    # Top layer: sources -> ingestion -> quality -> stores
    xs=[70,650,1230,1810,2390]; bw=500; top=170; bh=580
    colors=["#2563EB","#0891B2","#059669","#D97706","#7C3AED"]
    titles=["1. NGUỒN DỮ LIỆU","2. TIẾP NHẬN","3. KIỂM SOÁT CHẤT LƯỢNG","4. LƯU TRỮ","5. DỊCH VỤ AI / BI"]
    bodies=[
        "Tin việc: API/feed được phép\nNguồn nội địa được cấp quyền\nJD do nhà tuyển dụng đăng\nCV do ứng viên cung cấp\nGitHub qua OAuth, quyền tối thiểu\nESCO/O*NET và sự kiện",
        "API Consumer + Scheduler\nWebhook / sự kiện ứng viên\nKafka: job_raw, cv_events,\napplication_events\nGhi nguồn, thời điểm, phiên bản\nvà mã lần chạy",
        "Kiểm tra schema và trường bắt buộc\nChuẩn hóa HTML, địa điểm, tiền tệ\nKhử trùng lặp theo nội dung + URL\nPhát hiện tin lừa đảo, đưa nghi vấn\nvào hàng chờ duyệt\nNER kỹ năng và chuẩn hóa taxonomy",
        "S3 / MinIO: bản gốc có thời hạn\nPostgreSQL: hồ sơ, JD, đơn ứng tuyển\nQdrant: vector CV / JD / kỹ năng\nClickHouse: sự kiện BI đã ẩn danh\nMỗi bản ghi có source_id,\ntimestamps, quality_status",
        "Search API + bộ lọc điều kiện\nSemantic + Skill Matching\nSkill Gap / gợi ý học\nRecruiter ranking có giải thích\nBI Dashboard theo quyền truy cập"
    ]
    for i in range(5): box(d,(xs[i],top,xs[i]+bw,top+bh),titles[i],bodies[i],"#FFFFFF",colors[i],26,29)
    for i in range(4): arrow(d,(xs[i]+bw+8,top+bh/2),(xs[i+1]-10,top+bh/2))
    # query / response path
    box(d,(250,1000,1120,1500),"ỨNG VIÊN · TÌM VIỆC","1. Hồ sơ, kỹ năng, sở thích\n2. Từ khóa / bộ lọc / vị trí mong muốn\n3. Nhận danh sách việc làm, điểm phù hợp,\n   lý do gợi ý và kỹ năng còn thiếu","#EFF6FF","#1D4ED8",29,34)
    box(d,(1320,1000,2180,1500),"BỘ MÁY TRUY VẤN","Áp dụng bộ lọc bắt buộc trước\nTìm Top-K ứng viên bằng vector\nTính điểm đa yếu tố và confidence\nXếp hạng, giải thích, ghi impression\nKhông tự động loại hồ sơ chỉ bằng AI","#F5F3FF","#7C3AED",29,34)
    box(d,(2380,1000,2920,1500),"NHÀ TUYỂN DỤNG","Đăng JD và tiêu chí bắt buộc\nXem hồ sơ theo quyền được cấp\nTheo dõi phễu tuyển dụng\nXem BI đã tổng hợp / ẩn danh","#FFF7ED","#C2410C",27,32)
    arrow(d,(1120,1235),(1320,1235),"#2563EB",7)
    arrow(d,(1320,1410),(1120,1410),"#2563EB",7)
    text_center(d,(1220,1365),"Kết quả + lý do",font(22,True),"#1D4ED8")
    arrow(d,(2180,1190),(2380,1190),"#7C3AED",7)
    arrow(d,(2380,1410),(2180,1410),"#C2410C",7)
    text_center(d,(2280,1365),"JD / tiêu chí",font(22,True),"#C2410C")
    # storage/model relation
    arrow(d,(2060,750),(1760,1000),"#D97706",6)
    arrow(d,(2640,750),(2640,1000),"#7C3AED",6)
    d.multiline_text((120,1580),"Luồng đọc: truy vấn người dùng → kiểm tra quyền và bộ lọc → tìm kiếm / xếp hạng → trả kết quả có giải thích.\nLuồng ghi: lượt xem, lưu tin, ứng tuyển, phỏng vấn và kết quả tuyển dụng → sự kiện BI đã giảm định danh.",font=font(27),fill="#334155",spacing=8)
    im.save(path)

def diagram_etl(path):
    W,H=3000,1550
    im=Image.new("RGB",(W,H),"#F8FAFC"); d=ImageDraw.Draw(im)
    text_center(d,(W/2,65),"PIPELINE THU THẬP, LÀM SẠCH VÀ KIỂM SOÁT CHẤT LƯỢNG",font(46,True),"#0F172A")
    xs=[70,660,1250,1840,2430]; bw=500; y=180; h=940
    colors=["#0284C7","#059669","#7C3AED","#D97706","#475569"]
    titles=["1. INGESTION","2. VALIDATION","3. CLEANING","4. ENRICHMENT","5. PUBLISH"]
    bodies=[
      "• Pull theo lịch / webhook\n• Rate limit theo hợp đồng\n• Ghi source_id, fetched_at\n• Lưu raw có version\n• Retry lỗi tạm thời\n• Idempotency key",
      "• Schema + kiểu dữ liệu\n• Trường bắt buộc: title,\n  company, location, source URL\n• Kiểm tra consent / quyền repo\n• Chấm completeness score\n• Sai schema → quarantine",
      "• Chuẩn hóa Unicode / HTML\n• Chuẩn hóa địa danh, tiền tệ\n• Dedup URL + fingerprint JD\n• Tin nghi scam → review queue\n• Không tự suy đoán trường thiếu\n• Lưu lý do thay đổi",
      "• Trích xuất CV: PDF/DOCX/OCR\n• Skill NER + ESCO/O*NET ID\n• Tách must-have / nice-to-have\n• Tạo embedding có model_version\n• Duyệt AST trong sandbox\n• Ghi quality + confidence",
      "• PostgreSQL: dữ liệu tác nghiệp\n• Qdrant: embedding / metadata\n• ClickHouse: sự kiện BI\n• Chỉ phát hành bản hợp lệ\n• Theo dõi freshness / lag\n• Có thể replay từ raw"
    ]
    for i in range(5): box(d,(xs[i],y,xs[i]+bw,y+h),titles[i],bodies[i],"#FFFFFF",colors[i],27,32)
    for i in range(4): arrow(d,(xs[i]+bw+8,y+h/2),(xs[i+1]-10,y+h/2))
    # quality gate footer
    d.rounded_rectangle((120,1210,2880,1450),radius=25,fill="#ECFDF5",outline="#059669",width=4)
    text_center(d,(1500,1260),"QUALITY GATE TRƯỚC KHI CÔNG BỐ",font(32,True),"#047857")
    d.multiline_text((180,1310),"Đủ trường bắt buộc · URL truy vết được · dedup không vượt ngưỡng · trạng thái scam đã phân loại · kỹ năng có taxonomy/confidence\nTin hết hạn được ẩn · dữ liệu cá nhân có quyền truy cập / thời hạn lưu · bản ghi lỗi có hàng chờ sửa và audit log",font=font(27),fill="#14532D",spacing=10)
    im.save(path)

def diagram_match(path):
    W,H=3000,1120
    im=Image.new("RGB",(W,H),"#F8FAFC"); d=ImageDraw.Draw(im)
    text_center(d,(W/2,65),"LUỒNG SO KHỚP VIỆC LÀM VÀ GIẢI THÍCH KẾT QUẢ",font(46,True),"#0F172A")
    boxes=[
      (60,230,510,760,"A. HỒ SƠ ỨNG VIÊN","CV + học vấn + kỹ năng\nDự án đã xác minh\nĐịa điểm / hình thức làm\nMức lương mong muốn\nQuyền chia sẻ hồ sơ","#2563EB"),
      (620,230,1070,760,"B. HỒ SƠ CÔNG VIỆC","JD + công ty + vị trí\nMust-have / nice-to-have\nĐịa điểm / hình thức làm\nDải lương / ngày hết hạn\nNguồn và trạng thái tin","#0891B2"),
      (1180,230,1630,760,"C. ĐIỀU KIỆN CỨNG","Lọc trước theo quyền,\ntrạng thái còn tuyển,\nđịa điểm / remote, loại việc,\nngưỡng lương nếu có.\nKhông đủ dữ liệu? báo rõ.","#059669"),
      (1740,230,2190,760,"D. XẾP HẠNG HYBRID","45% độ phủ kỹ năng\n30% tương đồng ngữ nghĩa\n15% bằng chứng dự án\n10% phù hợp sở thích\nTách điểm phỏng vấn thành\nchỉ số readiness riêng","#7C3AED"),
      (2300,230,2940,760,"E. KẾT QUẢ CÓ GIẢI THÍCH","Điểm phù hợp + độ tin cậy\n3 kỹ năng khớp / còn thiếu\nLý do xếp hạng\nLiên kết nguồn / ngày đăng\nLưu lượt xem để đánh giá\nchất lượng gợi ý","#C2410C")
    ]
    for x1,y1,x2,y2,title,body,c in boxes: box(d,(x1,y1,x2,y2),title,body,"#FFFFFF",c,27,29)
    for i in range(4): arrow(d,(boxes[i][2]+8,495),(boxes[i+1][0]-10,495))
    d.multiline_text((90,880),"Match = 0,45 × SkillCoverage + 0,30 × SemanticSimilarity + 0,15 × VerifiedProject + 0,10 × PreferenceFit\nCác trọng số là cấu hình khởi đầu; cần hiệu chỉnh theo dữ liệu đánh giá có kiểm soát. Điểm AI hỗ trợ quyết định, không tự động từ chối ứng viên.",font=font(29),fill="#334155",spacing=12)
    im.save(path)

def diagram_star(path):
    W,H=2800,2000
    im=Image.new("RGB",(W,H),"#F8FAFC"); d=ImageDraw.Draw(im)
    text_center(d,(W/2,70),"STAR SCHEMA VÀ BRIDGE TABLE CHO PHÂN TÍCH KỸ NĂNG",font(45,True),"#0F172A")
    # central fact
    box(d,(900,590,1900,1330),"FACT_APPLICATION","PK: application_id\nFK: student_key, job_key, company_key, time_key\nMeasures: match_score, response_days,\ninterview_score, hired_flag, stage_count\nDegenerate: source_channel, application_status\nGrain: một dòng cho một lần ứng tuyển","#E0F2FE","#1D4ED8",31,36)
    dims=[
      (100,300,780,760,"DIM_STUDENT","student_key (surrogate PK)\nuniversity, major, graduation_year\nconsent_status, profile_cohort\nPII nằm riêng, phân quyền hạn chế","#2563EB"),
      (2020,300,2700,760,"DIM_JOB","job_key, title, level, work_type\nlocation, salary_band, posted_at\nsource_id, expiry_at, verified_status","#0891B2"),
      (100,1130,780,1580,"DIM_TIME","time_key, date, week, month\nquarter, year, academic_term","#7C3AED"),
      (2020,1130,2700,1580,"DIM_COMPANY","company_key, industry, size_band\nverification_status, region","#D97706"),
      (950,1500,1850,1830,"BRIDGE_JOB_SKILL","job_key + skill_key\nrequirement_type: must / nice\nimportance_weight, taxonomy_id\nresolves many-to-many skills","#059669"),
      (2020,1610,2700,1850,"DIM_SKILL","skill_key, canonical_name\ntaxonomy_id, category, version","#0F766E")
    ]
    for x1,y1,x2,y2,t,b,c in dims: box(d,(x1,y1,x2,y2),t,b,"#FFFFFF",c,25,27)
    arrow(d,(780,530),(900,760)); arrow(d,(2020,530),(1900,760)); arrow(d,(780,1350),(900,1190)); arrow(d,(2020,1350),(1900,1190))
    arrow(d,(1400,1500),(1400,1330)); arrow(d,(2020,1730),(1850,1660))
    d.text((100,1900),"Fact được nạp theo batch từ sự kiện ứng tuyển; dimension dùng surrogate key và lưu lịch sử thay đổi khi cần phân tích theo thời điểm.",font=font(26),fill="#334155")
    im.save(path)

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)

def set_cell_text(cell, text, bold=False, color=None, size=9):
    cell.text=''
    p=cell.paragraphs[0]
    p.paragraph_format.space_after=Pt(2)
    r=p.add_run(str(text)); r.bold=bold; r.font.size=Pt(size)
    if color: r.font.color.rgb=RGBColor(*color)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def set_repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr(); tblHeader=OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'),'true'); trPr.append(tblHeader)

def add_table(doc, headers, rows, widths=None):
    table=doc.add_table(rows=1, cols=len(headers)); table.style='Table Grid'; table.alignment=WD_TABLE_ALIGNMENT.CENTER
    set_repeat_table_header(table.rows[0])
    for i,h in enumerate(headers): set_cell_text(table.rows[0].cells[i],h,True,(255,255,255),9); shade(table.rows[0].cells[i],'1F4E78')
    for ridx,row in enumerate(rows):
        cells=table.add_row().cells
        for i,val in enumerate(row):
            set_cell_text(cells[i],val,False,None,8.5)
            if ridx%2==1: shade(cells[i],'F1F5F9')
    if widths:
        for row in table.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    doc.add_paragraph()
    return table

def add_bullet(doc, text):
    p=doc.add_paragraph(style='List Bullet'); p.paragraph_format.space_after=Pt(3); p.add_run(text)

def replace_text_in_runs(paragraph, old, new):
    full=paragraph.text
    start=full.find(old)
    if start < 0: return False
    end=start+len(old); positions=[]; cursor=0
    for run in paragraph.runs:
        positions.append((cursor,cursor+len(run.text)))
        cursor+=len(run.text)
    first=next(i for i,(a,b) in enumerate(positions) if a<=start<b or (a==b==start))
    last=next(i for i,(a,b) in enumerate(positions) if a<end<=b or (a==b==end))
    first_a,first_b=positions[first]; last_a,last_b=positions[last]
    if first==last:
        run=paragraph.runs[first]
        run.text=run.text[:start-first_a]+new+run.text[end-first_a:]
    else:
        paragraph.runs[first].text=paragraph.runs[first].text[:start-first_a]+new
        for i in range(first+1,last): paragraph.runs[i].text=''
        paragraph.runs[last].text=paragraph.runs[last].text[end-last_a:]
    return True

def add_figure(doc, image, caption, width=6.2):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image),width=Inches(width))
    cap=doc.add_paragraph(caption); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    if cap.runs: cap.runs[0].italic=True; cap.runs[0].font.size=Pt(9)

def main():
    etl=DIAGRAMS/'diagram_etl_detailed.png'; dfd=DIAGRAMS/'dfd_data_flow_detailed.png'; match=DIAGRAMS/'diagram_matching_detailed.png'; star=DIAGRAMS/'diagram_star_schema_detailed.png'
    diagram_etl(etl); diagram_dfd(dfd); diagram_match(match); diagram_star(star)
    doc=Document(DOC_IN)
    # Existing paragraphs used both Word's list bullet and a typed bullet glyph.
    # Remove the duplicate glyph while retaining the original run formatting.
    for p in doc.paragraphs:
        if p.style.name.startswith('List Bullet') and p.text.lstrip().startswith('•'):
            for run in p.runs:
                if run.text.strip():
                    run.text=run.text.replace('•','',1).lstrip()
                    break
        text=p.text
        replacements={
          'tỷ lệ phản hồi dưới 5%.':'tỷ lệ phản hồi thấp; cần đo bằng mẫu khảo sát có nguồn và thời gian cụ thể.',
          '70% CV sinh viên chứa thông tin phóng đại, đồ án copy từ mã nguồn mở không phản ánh đúng năng lực lập trình thực tế.':'một số CV có thể phóng đại năng lực hoặc mô tả đồ án thiếu bằng chứng kiểm chứng; hệ thống cần hỗ trợ đối chiếu thay vì mặc định hồ sơ không trung thực.',
          'Mất trung bình 45 - 60 ngày và tiêu tốn nhiều vòng phỏng vấn kỹ thuật chỉ để sàng lọc một ứng viên đạt chuẩn cơ bản.':'Quy trình có thể kéo dài nhiều tuần và tiêu tốn nhiều vòng phỏng vấn; thời gian thực tế cần được đo theo từng doanh nghiệp và vị trí.',
          'Độ tin cậy đạt 99%, ít rác.':'Dữ liệu thường có cấu trúc hơn nguồn crawl; độ đầy đủ và độ tin cậy cần được đo theo từng API / đối tác.',
          'Thu thập 10.000+ tin tuyển dụng thực tế tại thị trường Việt Nam.':'Mục tiêu tăng độ phủ nguồn tuyển dụng sau khi xác nhận quyền sử dụng và đo được tỷ lệ tin còn hiệu lực.',
          'Chuẩn hóa 13.800+ thực thể kỹ năng, liên kết từ đồng nghĩa công nghệ.':'Chuẩn hóa kỹ năng theo taxonomy và phiên bản dữ liệu được lựa chọn; lưu ID và từ đồng nghĩa có nguồn gốc.',
          'cho hơn 13.800 kỹ năng công nghệ.':'số lượng khái niệm được xác định theo phiên bản dữ liệu thực tế được nạp.',
          "đều được định danh về một mã chuẩn `ESCO:IT:0842`.":"được ánh xạ về URI chính thức nếu taxonomy xác nhận khái niệm tương ứng.",
          'độ trễ < 50ms.':'mục tiêu thử nghiệm p95 dưới 50 ms với tải và hạ tầng được ghi rõ.',
          'trong vòng 15ms.':'mục tiêu thử nghiệm p95 dưới 15 ms với quy mô dữ liệu và phần cứng được ghi rõ.',
          'sử dụng kỹ thuật nội suy (Imputation) dựa trên vị trí tương đương nếu tin tuyển dụng để \'Thỏa thuận\'.':'không tự điền lương khi nguồn ghi \'Thỏa thuận\'; nếu cần hiển thị ước tính thị trường thì lưu ở trường riêng, kèm nhãn và phương pháp tính.',
          'Mô hình phân loại văn bản (Text Classifier) được huấn luyện trên tập dữ liệu tin rác thực tế.':'Mô hình phân loại văn bản được đánh giá trên tập tin tuyển dụng đã gán nhãn; các tin điểm rủi ro cao chuyển cho người duyệt thay vì bị xóa tự động.',
        }
        for old,new in replacements.items():
            replace_text_in_runs(p,old,new)
        replace_text_in_runs(p,'Crawl-delay >= 2 giây','tần suất theo chính sách từng nguồn / thỏa thuận')
        if p.text.startswith('2. Cơ Chế Quy Đổi Đồ Án Thành Kinh Nghiệm'):
            p.runs[0].text='2. Đánh Giá Bằng Chứng Dự Án (Project Evidence Assessment): '
            p.runs[1].text='Hệ thống phân tích repository do ứng viên chọn, lịch sử commit, công nghệ và kết quả kiểm tra trong sandbox để tạo hồ sơ năng lực dự án có nguồn gốc. Điểm này giúp nhà tuyển dụng xem xét kinh nghiệm học thuật; không quy đổi tự động thành số tháng hoặc số năm làm việc.'
        if p.text.startswith('3. Thẩm Định Mã Nguồn Tự Động'):
            p.runs[1].text='Kết nối repository do ứng viên chủ động chọn và cấp quyền. Phân tích tĩnh theo ngôn ngữ được hỗ trợ, tạo chỉ số tham khảo về cấu trúc, độ phức tạp, kiểm thử và đoạn mã tương tự. Báo cáo giữ liên kết tới repository, commit và phiên bản công cụ; đây là tín hiệu hỗ trợ, không phải chứng nhận tuyệt đối và không tự động loại hồ sơ.'
        if p.text.startswith('4. Buồng Luyện Phỏng Vấn Giọng Nói'):
            p.runs[1].text='Mô hình AI tương tác đàm thoại theo JD. Hệ thống đánh giá nội dung câu trả lời và cấu trúc lập luận. Phân tích tốc độ nói hoặc từ ngập ngừng chỉ bật khi người dùng đồng ý; không suy đoán năng lực từ âm sắc, giọng vùng miền hay đặc điểm giọng nói.'
        if p.text.startswith('2. Khử trùng lặp đa nguồn'):
            # Replace the fragile auto-merge claim while keeping the bold leading label.
            if len(p.runs)>1:
                p.runs[-1].text='Một công việc có thể xuất hiện ở nhiều nguồn với tiêu đề khác nhau. Hệ thống tạo fingerprint nội dung và so sánh URL, công ty, vị trí, địa điểm. Bản ghi chỉ được tự động gộp khi ngưỡng đã hiệu chỉnh và các trường định danh đồng thuận; trường hợp mâu thuẫn chuyển duyệt. Mỗi cụm giữ các URL nguồn và lịch sử thay đổi.'
        if 'Cấp Chứng chỉ thẩm định tự động' in p.text:
            replace_text_in_runs(p,'Cấp Chứng chỉ thẩm định tự động loại bỏ hoàn toàn CV ảo.','Tạo báo cáo phân tích có thể kiểm tra lại; kết quả không phải chứng nhận tuyệt đối và không tự động loại hồ sơ.')
        if p.text.startswith('e) Nguồn Chuẩn hóa Kỹ năng O*NET'):
            new_p=OxmlElement('w:p'); p._p.addnext(new_p)
            added=Paragraph(new_p,p._parent); added.style='List Bullet'
            r=added.add_run('f) Nguồn Nhật ký Tương tác & Lịch sử Ứng tuyển: Ghi nhận lượt xem, lưu tin, bắt đầu / gửi đơn, trạng thái phỏng vấn và kết quả tuyển dụng. Mỗi sự kiện có event_id, loại sự kiện, thời điểm, job_id, mã người dùng đã giả danh và phiên bản mục đích sử dụng. Dữ liệu này phục vụ BI và đánh giá gợi ý; không đưa thông tin liên hệ hoặc nội dung CV vào event stream.')
            r.font.size=Pt(10)
    # Correct the operational collection language and keep the six sources consistent.
    for p in doc.paragraphs:
        if 'cụm Scrapy phân tán kết hợp cơ chế luân phiên Proxy' in p.text:
            p.text=p.text.replace('Hệ thống triển khai cụm Scrapy phân tán kết hợp cơ chế luân phiên Proxy (Rotating Residential Proxies) và User-Agent để vượt qua các lớp bảo vệ chống cào dữ liệu (Cloudflare, CAPTCHA).','Hệ thống ưu tiên API, RSS/feed hoặc thỏa thuận cung cấp dữ liệu. Chỉ thu thập website khi điều khoản và quyền truy cập cho phép; tôn trọng robots.txt, giới hạn tốc độ và cơ chế từ chối truy cập. Không vượt CAPTCHA, paywall hoặc biện pháp kiểm soát truy cập. Khi nguồn thay đổi cấu trúc, tạm dừng crawler và đưa lỗi vào hàng chờ xử lý.')
        if p.text.startswith('2.2. Đánh Giá Rủi Ro'):
            pass
        if 'sử dụng kỹ thuật nội suy (Imputation) dựa trên vị trí tương đương nếu tin tuyển dụng để \'Thỏa thuận\'' in p.text:
            p.text=p.text.replace("sử dụng kỹ thuật nội suy (Imputation) dựa trên vị trí tương đương nếu tin tuyển dụng để 'Thỏa thuận'.", "không tự điền lương khi nguồn ghi 'Thỏa thuận'; nếu cần hiển thị ước tính thị trường thì lưu ở trường riêng, kèm nhãn và phương pháp tính.")
    # Replace formula table text so the matching definition is consistent and interpretable.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                original=cell.text
                updated=original.replace('độ trễ < 50ms.','mục tiêu thử nghiệm p95 dưới 50 ms với tải và hạ tầng được ghi rõ.')
                updated=updated.replace('trong vòng 15ms.','mục tiêu thử nghiệm p95 dưới 15 ms với quy mô dữ liệu và phần cứng được ghi rõ.')
                updated=updated.replace('Thu thập 10.000+ tin tuyển dụng thực tế tại thị trường Việt Nam.','Tăng độ phủ nguồn việc làm theo quyền sử dụng và tỷ lệ tin còn hiệu lực.')
                updated=updated.replace('Chuẩn hóa 13.800+ thực thể kỹ năng, liên kết từ đồng nghĩa công nghệ.','Chuẩn hóa kỹ năng theo taxonomy, phiên bản, ID và từ đồng nghĩa có nguồn gốc.')
                if updated!=original: cell.text=updated
                if 'Match_Score = (0.55 × Cosine_Similarity)' in cell.text:
                    cell.text='CÔNG THỨC SO KHỚP ĐA CHIỀU (KHỞI ĐIỂM): Match_Score = 0,45 × SkillCoverage + 0,30 × SemanticSimilarity + 0,15 × VerifiedProject + 0,10 × PreferenceFit. Các tiêu chí bắt buộc (tin còn hạn, loại việc, địa điểm, ngưỡng lương nếu có) được áp dụng trước khi xếp hạng. Điểm phỏng vấn Voice AI được báo cáo riêng dưới dạng Readiness Score, không làm giảm điểm phù hợp việc làm khi ứng viên chưa phỏng vấn. Trọng số cần được hiệu chỉnh bằng dữ liệu đánh giá có kiểm soát.'
                if cell.text.strip() in ('Qdrant / Milvus','Qdrant / Milvus (Vector DB)'):
                    cell.text='Qdrant (chính); Milvus chỉ sau POC'
    doc.add_page_break()
    doc.add_heading('PHỤ LỤC THIẾT KẾ CHI TIẾT',level=1)
    doc.add_paragraph('Phụ lục này cụ thể hóa các quyết định vận hành, trường dữ liệu, quy tắc chất lượng và luồng xử lý để bản đề xuất có thể chuyển thành thiết kế thử nghiệm. Các ngưỡng hiệu năng dưới đây là mục tiêu ban đầu cần đo trên dữ liệu thử nghiệm, không phải kết quả đã được kiểm chứng.')

    doc.add_heading('A. Đặc tả đối tượng và hành trình sử dụng',level=2)
    add_table(doc,['Đối tượng','Nhu cầu / điểm đau','Dữ liệu đầu vào','Kết quả hệ thống','Chỉ số đánh giá'],[
      ['Ứng viên năm cuối / fresher','Khó diễn giải đồ án thành năng lực; không biết kỹ năng nào còn thiếu; khó tìm tin phù hợp.','CV, kỹ năng, học vấn, dự án, sở thích việc làm; repo GitHub chỉ khi tự nguyện cấp quyền.','Danh sách việc phù hợp có lý do; kỹ năng còn thiếu; trạng thái ứng tuyển; báo cáo kỹ năng có thể kiểm tra lại.','Tỷ lệ hồ sơ hoàn chỉnh; tỷ lệ nhấp vào tin được gợi ý; tỷ lệ ứng tuyển phù hợp; phản hồi hữu ích của người dùng.'],
      ['Nhà tuyển dụng / HR','Nhiều hồ sơ cần sàng lọc; tiêu chí tuyển dụng không luôn được viết rõ; thiếu tín hiệu năng lực thống nhất.','JD, tiêu chí bắt buộc / ưu tiên, địa điểm, loại hình, dải lương, trạng thái tuyển.','Danh sách ứng viên xếp hạng kèm tiêu chí khớp, khoảng trống và bằng chứng; thống kê quy trình.','Thời gian xem xét hồ sơ; tỷ lệ chuyển vòng; tỷ lệ tuyển; mức độ đồng thuận giữa người đánh giá.'],
      ['Trường / cố vấn nghề nghiệp','Khó cập nhật nhu cầu kỹ năng theo thị trường và hỗ trợ sinh viên theo dữ liệu.','Dữ liệu tổng hợp về kỹ năng, JD, ứng tuyển; nhóm ngành / khóa học nếu có căn cứ và quyền dùng.','Dashboard tổng hợp theo ngành, thời gian, khu vực; gợi ý nội dung đào tạo ở cấp nhóm.','Độ phủ dữ liệu; độ mới; số người dùng báo cáo; không tiết lộ cá nhân trong nhóm nhỏ.']
    ],[1.05,1.4,1.5,1.45,1.2])
    doc.add_heading('Hành trình chính của ứng viên',level=3)
    for t in [
      'Tạo tài khoản và chọn quyền riêng tư; hệ thống chỉ yêu cầu trường cần cho tìm việc. Hồ sơ có thể ẩn danh với nhà tuyển dụng cho đến khi ứng viên chủ động nộp đơn hoặc chia sẻ.',
      'Tải CV lên, xem lại các trường hệ thống trích xuất và sửa sai. Mỗi trường trích xuất lưu nguồn (CV / người dùng xác nhận), thời điểm cập nhật và độ tin cậy.',
      'Tùy chọn kết nối GitHub qua OAuth với phạm vi quyền đọc tối thiểu. Ứng viên chọn repository cần phân tích; không clone repository riêng tư nếu chưa có quyền rõ ràng.',
      'Nhập tiêu chí tìm việc và xem kết quả. Mỗi gợi ý giải thích kỹ năng phù hợp, kỹ năng còn thiếu, điều kiện đã lọc và nguồn đăng tin.',
      'Khi ứng tuyển, hệ thống lưu bản CV được gửi, thời điểm, vị trí và trạng thái. Ứng viên có thể rút quyền chia sẻ và yêu cầu xóa dữ liệu theo quy trình đã công bố.'
    ]: add_bullet(doc,t)
    doc.add_heading('Hành trình chính của nhà tuyển dụng',level=3)
    for t in [
      'Xác minh tổ chức và quyền của người đăng; tách rõ người xem hồ sơ, người sửa JD và người quản trị.',
      'Đăng JD theo cấu trúc: chức danh, cấp bậc, địa điểm / remote, hình thức làm, dải lương, ngày hết hạn, must-have, nice-to-have và nguồn / người phê duyệt.',
      'Xem danh sách ứng viên với lý do xếp hạng, nguồn bằng chứng và độ tin cậy; người tuyển dụng quyết định chuyển vòng, không để mô hình tự động từ chối.',
      'Cập nhật kết quả từng vòng để theo dõi funnel. Dashboard chỉ hiển thị dữ liệu tổng hợp theo nhóm đủ lớn và theo quyền.'
    ]: add_bullet(doc,t)

    doc.add_heading('B. Từ điển nguồn dữ liệu và trường cần thu thập',level=2)
    add_table(doc,['Nguồn','Trường dữ liệu cốt lõi','Cập nhật / kiểm tra','Quy tắc sử dụng'],[
      ['API / feed việc làm có quyền truy cập','source_job_id, title, company, location, work_type, salary_min/max/currency, description, posted_at, expires_at, source_url.','Theo lịch do nguồn cho phép; kiểm tra schema, ngày hết hạn, URL và trạng thái tuyển.','Lưu source_id và license / agreement; không giả định API công khai luôn cấp quyền truy cập.'],
      ['Website tuyển dụng được phép crawl','URL chuẩn, title, công ty, địa điểm, loại việc, mô tả, lương, thời gian đăng, thời gian lấy, trạng thái parse.','Crawl-delay theo chính sách nguồn; parser có version; lỗi DOM vào quarantine.','Không vượt kiểm soát truy cập; giới hạn trường ở thông tin tin tuyển dụng công khai.'],
      ['CV / hồ sơ do người dùng cung cấp','Tên hiển thị; liên hệ; học vấn; kỹ năng; kinh nghiệm; chứng chỉ; ngôn ngữ; consent_version.','Khi người dùng tải / sửa; lưu kết quả trích xuất, độ tin cậy và xác nhận của người dùng.','Tách PII khỏi chỉ mục tìm kiếm; mã hóa, kiểm soát quyền và thời hạn lưu.'],
      ['GitHub qua OAuth','provider_user_id, repository_id, ngôn ngữ, file được chọn, commit metadata, chỉ số phân tích.','Webhook hoặc yêu cầu phân tích chủ động; giới hạn tần suất và kích cỡ repo.','Quyền tối thiểu; không lưu token dài hạn dạng rõ; không lưu nội dung nhạy cảm trong log.'],
      ['ESCO / O*NET','taxonomy_id, canonical label, synonym, occupation / skill relation, language, version.','Theo phiên bản dữ liệu công bố; tạo bảng mapping và lưu version.','Giữ nguyên nguồn và giấy phép; không gán mã chuẩn nếu không đủ độ tin cậy.'],
      ['Sự kiện sử dụng','event_id, pseudonymous_user_id, job_id, event_type, timestamp, experiment_id, consent / purpose.','Streaming; kiểm tra schema, event duplication và đồng bộ thời gian.','Không đưa email / điện thoại vào event; chỉ giữ sự kiện cần cho vận hành và đánh giá.']
    ],[1.15,2.2,1.55,1.75])
    doc.add_paragraph('Bộ trường tối thiểu cho một JD có thể đưa vào tìm kiếm: job_id, source_id, source_url, title, company_name, description, location hoặc remote_type, employment_type, posted_at, expiry_at, status, ingest_timestamp. Salary có thể để trống; không điền mức lương suy đoán vào trường salary do nhà tuyển dụng cung cấp. Nếu hiển thị ước tính thị trường, phải là trường riêng, kèm phương pháp, ngày tính và nhãn “ước tính”.')

    doc.add_heading('C. Pipeline ETL và quy tắc kiểm soát chất lượng',level=2)
    add_table(doc,['Bước','Kiểm tra / biến đổi','Điều kiện đạt','Nếu không đạt'],[
      ['Ingestion','Ghi source_id, fetched_at, source_record_id, batch_id, parser_version; lưu raw có checksum.','Bản ghi truy vết được về nguồn và lần lấy.','Retry lỗi tạm thời; lỗi quyền / schema không retry vô hạn, tạo cảnh báo.'],
      ['Validation','Kiểm tra loại dữ liệu, bắt buộc, độ dài, ngày, URL, mã tiền tệ, trạng thái tuyển.','Các trường bắt buộc hợp lệ; lỗi tùy chọn được gắn nhãn.','Quarantine; không trộn bản ghi không hợp lệ vào chỉ mục.'],
      ['Cleaning / dedup','Chuẩn hóa khoảng trắng / HTML / địa danh; canonical URL; fingerprint mô tả; giữ liên kết nhiều nguồn.','Bản ghi chuẩn và cụm trùng có evidence.','Đánh dấu nghi trùng để duyệt nếu điểm gần ngưỡng; không tự gộp khi công ty / vị trí mâu thuẫn.'],
      ['Enrichment','Skill NER, taxonomy mapping, embedding, đánh giá scam / code.','Ghi model_version, taxonomy_version, confidence và kết quả phân tích.','Kỹ năng độ tin cậy thấp gắn nhãn chưa xác nhận; tin scam nghi vấn chuyển review.'],
      ['Publish / monitor','Nạp sang PostgreSQL / Qdrant / ClickHouse; cập nhật chỉ mục; theo dõi freshness, lỗi, độ trễ.','Bản ghi được kiểm tra sau nạp; job chưa hết hạn; chất lượng đạt ngưỡng.','Rollback bản lỗi; replay từ raw; phát cảnh báo theo nguồn / pipeline stage.']
    ],[0.9,2.3,1.5,1.9])
    doc.add_heading('Chỉ số chất lượng cần theo dõi',level=3)
    add_table(doc,['Chỉ số','Cách tính','Mục tiêu khởi điểm / hành động'],[
      ['Completeness','Số trường bắt buộc hợp lệ / tổng trường bắt buộc.','≥ 95% cho bản ghi phát hành; thấp hơn thì giữ lại hoặc cảnh báo nguồn.'],
      ['Freshness','Thời điểm hiện tại trừ fetched_at / posted_at; tỷ lệ tin còn hạn.','Đặt theo hợp đồng nguồn; ẩn tin hết hạn và hiển thị thời điểm cập nhật.'],
      ['Duplicate rate','Số bản ghi được ghép trùng / số bản ghi nhận.','Theo dõi theo từng nguồn; mẫu bất thường kích hoạt rà lại fingerprint.'],
      ['Parse success','Bản ghi parse được / bản ghi đã tải.','Cảnh báo khi giảm đột ngột; rollback parser nếu schema nguồn đổi.'],
      ['Taxonomy confidence','Tỷ lệ kỹ năng ánh xạ chắc chắn / tổng kỹ năng trích xuất.','Từ chối mapping tự động dưới ngưỡng; cho phép người dùng xác nhận.'],
      ['Scam false positive','Tin hợp lệ bị gắn cờ / tin đã gắn cờ được duyệt.','Lấy mẫu người duyệt; chỉnh ngưỡng theo mức thiệt hại và phản hồi.']
    ],[1.25,2.5,2.85])
    doc.add_heading('Quy tắc lưu trữ và bảo vệ dữ liệu',level=3)
    for t in [
      'Raw zone lưu tách biệt và có lịch xóa theo loại dữ liệu; dữ liệu CV không được lưu vô thời hạn chỉ vì có thể chạy lại pipeline.',
      'PostgreSQL giữ hồ sơ, JD, đơn và trạng thái; PII có bảng / service tách biệt, mã hóa khi lưu và khi truyền, quyền truy cập theo vai trò.',
      'Qdrant chỉ lưu embedding, loại đối tượng, id tham chiếu, model_version và metadata tối thiểu. Xóa hồ sơ cần xóa hoặc vô hiệu embedding tương ứng.',
      'ClickHouse nhận sự kiện pseudonymized; không gửi email, số điện thoại hay nội dung CV. Dashboard áp dụng ngưỡng ẩn nhóm nhỏ để giảm nguy cơ suy ra danh tính.',
      'Mọi lần đọc / tải CV, thay đổi quyền, xóa dữ liệu, xuất báo cáo và thay đổi trạng thái ứng tuyển đều ghi audit log có thời hạn lưu xác định.'
    ]: add_bullet(doc,t)

    doc.add_heading('D. Luồng tìm kiếm và logic xếp hạng',level=2)
    add_figure(doc,match,'Hình D1. Luồng so khớp tách điều kiện bắt buộc khỏi xếp hạng phù hợp.',6.2)
    add_table(doc,['Thành phần điểm','Tỷ trọng ban đầu','Định nghĩa'],[
      ['SkillCoverage','45%','Tỷ lệ kỹ năng bắt buộc và ưu tiên được xác nhận; must-have có trọng số cao hơn nice-to-have.'],
      ['SemanticSimilarity','30%','Độ gần vector giữa hồ sơ đã chuẩn hóa và JD; so sánh trong cùng phiên bản embedding.'],
      ['VerifiedProject','15%','Bằng chứng dự án do ứng viên chọn và cho phép phân tích; điểm dựa trên rubric có giải thích.'],
      ['PreferenceFit','10%','Mức phù hợp với địa điểm, hình thức, loại việc và mức lương kỳ vọng đã khai báo.'],
      ['ReadinessScore','Không cộng vào Match','Kết quả luyện phỏng vấn; trình bày riêng và chỉ có khi người dùng chủ động tham gia.']
    ],[1.5,1.2,3.9])
    doc.add_paragraph('Bộ lọc điều kiện cứng chạy trước công thức: tin còn mở, loại hình làm việc, địa điểm / remote và yêu cầu pháp lý được nhà tuyển dụng cấu hình. Nếu thiếu lương hoặc một kỹ năng không chắc chắn, giao diện phải chỉ ra dữ liệu chưa có thay vì xem như không phù hợp. Mỗi kết quả trả về các yếu tố đóng góp vào điểm và đường dẫn nguồn tin.')
    doc.add_heading('Thứ tự xử lý một truy vấn',level=3)
    for t in [
      'Xác thực người dùng, quyền xem hồ sơ và trạng thái consent; lấy hồ sơ đã được xác nhận.',
      'Chuẩn hóa từ khóa / bộ lọc; xác định điều kiện cứng và danh sách việc còn hạn.',
      'Truy vấn vector lấy Top-K ứng viên; thực hiện tìm kiếm từ khóa bổ sung để giữ các tên kỹ thuật chính xác.',
      'Tính điểm từng thành phần, kiểm tra độ tin cậy và tránh dùng trường nhạy cảm hoặc proxy không liên quan đến năng lực.',
      'Trả danh sách theo thứ tự, lý do gợi ý, kỹ năng còn thiếu, ngày cập nhật và nguồn; ghi impression để tính độ hữu ích.',
      'Khi người dùng lưu tin / ứng tuyển / bỏ qua, ghi event tối thiểu; phản hồi này dùng đánh giá chất lượng gợi ý theo nhóm, không lập tức làm thay đổi điểm cá nhân thiếu kiểm soát.'
    ]: add_bullet(doc,t)

    doc.add_heading('E. DFD chi tiết và mô hình BI',level=2)
    add_table(doc,['Bảng BI','Grain / khóa','Ví dụ chỉ số'],[
      ['FACT_APPLICATION','Một dòng cho một lần ứng tuyển; khóa ứng viên, việc làm, công ty, thời gian.','Tỷ lệ qua vòng, thời gian phản hồi, tỷ lệ nhận offer / tuyển.'],
      ['DIM_STUDENT','Một phiên bản hồ sơ ứng viên theo chính sách ẩn danh.','Nhóm ngành, khóa tốt nghiệp, trường ở mức tổng hợp.'],
      ['DIM_JOB / DIM_COMPANY','Một việc làm / một công ty được chuẩn hóa.','Nhu cầu kỹ năng, mức lương, khu vực, ngành.'],
      ['DIM_TIME','Một ngày / tuần / tháng / học kỳ.','Xu hướng theo thời gian và mùa tuyển dụng.'],
      ['DIM_SKILL + BRIDGE_JOB_SKILL','Một kỹ năng chuẩn và quan hệ kỹ năng với JD; bridge giữ must-have / nice-to-have.','Độ lệch cung-cầu, kỹ năng thường đi cùng nhau, biến động nhu cầu.']
    ],[1.4,2.75,2.45])
    doc.add_paragraph('Không xuất dashboard theo cá nhân nếu người xem không có quyền nghiệp vụ. Các số liệu về tỷ lệ tuyển dụng, cung-cầu kỹ năng và mức lương phải nêu kỳ thời gian, quy mô mẫu, nguồn dữ liệu, cách xử lý tin trùng và độ phủ mẫu.')

    doc.add_heading('F. Kế hoạch thử nghiệm và tiêu chí nghiệm thu đề xuất',level=2)
    add_table(doc,['Giai đoạn','Phạm vi','Tiêu chí nghiệm thu'],[
      ['1. Dữ liệu mẫu có quyền sử dụng','Một nhóm ngành, một khu vực; API/feed hoặc dữ liệu tuyển dụng được phép; CV giả lập / có consent.','Tỷ lệ parse, completeness, dedup, độ mới và hàng chờ lỗi được đo; có thể truy nguyên từng bản ghi.'],
      ['2. Tìm kiếm cơ bản','Hồ sơ ứng viên, bộ lọc cứng, truy vấn keyword + vector.','Kết quả không chứa tin hết hạn; người dùng hiểu lý do; so sánh top 10 với đánh giá thủ công.'],
      ['3. Xếp hạng có giải thích','SkillCoverage, SemanticSimilarity, Project evidence, PreferenceFit.','Đánh giá precision@10 / nDCG@10 trên bộ gán nhãn; kiểm tra chênh lệch theo nhóm; lưu phiên bản trọng số.'],
      ['4. Hành trình ứng tuyển','Lưu / ứng tuyển / trạng thái, quyền chia sẻ CV.','Ứng viên xem được CV gửi; nhà tuyển dụng chỉ thấy hồ sơ đã được chia sẻ; audit log đầy đủ.'],
      ['5. BI','Dữ liệu sự kiện pseudonymized và Star Schema.','Đối soát số lượng đơn; dashboard ghi rõ kỳ, mẫu, định nghĩa metric và quyền xem.']
    ],[1.2,2.3,3.1])
    doc.add_paragraph('Các chỉ số về thời gian phản hồi, mức tăng tỷ lệ trúng tuyển hay độ trễ truy vấn chỉ được trình bày như kết quả sau khi chạy thử nghiệm có ghi nhận kích thước dữ liệu, phần cứng, thời điểm đo và phương pháp tính. Trước đó, ghi rõ là mục tiêu thiết kế.')

    doc.add_heading('G. Tài liệu tham khảo kỹ thuật và dữ liệu',level=2)
    refs=[
      'Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP-IJCNLP. https://aclanthology.org/D19-1410/',
      'European Commission. ESCO Classification: skills, competences and occupations; phiên bản dữ liệu cần được ghi rõ trong mỗi lần nạp. https://esco.ec.europa.eu/en/classification',
      'O*NET Resource Center. O*NET Database Releases and License. Chọn phiên bản và tuân thủ attribution / license của dữ liệu sử dụng. https://www.onetcenter.org/db_releases.html ; https://www.onetcenter.org/license_db.html',
      'Apache Software Foundation. Apache Kafka Documentation. https://kafka.apache.org/documentation/',
      'Qdrant. Search and hybrid retrieval documentation. https://qdrant.tech/documentation/search/',
      'Chính phủ Việt Nam. Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân. https://vanban.chinhphu.vn/?classid=0&docid=207759&pageid=27160',
    ]
    for i,ref in enumerate(refs,1):
        p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
        r=p.add_run(f'{i}. {ref}'); r.font.size=Pt(8.5)
    p=doc.add_paragraph('Ngày truy cập các nguồn trực tuyến: 22/10/2026. Với API tuyển dụng thương mại, cần bổ sung tài liệu quyền truy cập / điều khoản của từng đối tác trước khi triển khai.')
    p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
    for r in p.runs: r.font.size=Pt(8.5)

    # Replace old inline figures at the three known figure positions with clearer versions.
    replacements={
      'Hình 3.1: Quy trình Thu thập':etl,
      'Hình 4.1: Sơ đồ Luồng Dữ Liệu Tổng Thể':dfd,
      'Hình 4.2: Mô hình Kho dữ liệu Star Schema':star,
    }
    # Locate each caption, remove its old image paragraph, and insert replacement immediately before it.
    for caption,img in replacements.items():
        para=next(p for p in doc.paragraphs if p.text.startswith(caption))
        prev=para._p.getprevious()
        if prev is not None and prev.xpath('.//wp:inline'):
            old=Paragraph(prev,doc._body)
            old._p.getparent().remove(old._p)
            newp=para.insert_paragraph_before()
            newp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            newp.add_run().add_picture(str(img),width=Inches(6.2))
    # Set useful metadata and save.
    # Keep table rows intact across page breaks so checklist and data-dictionary rows stay readable.
    for table in doc.tables:
        for row in table.rows:
            trPr=row._tr.get_or_add_trPr()
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(OxmlElement('w:cantSplit'))
    doc.core_properties.title='Đề xuất hệ thống tìm kiếm việc làm thông minh và chiến lược dữ liệu bản chi tiết'
    doc.core_properties.subject='Thiết kế hệ thống, nguồn dữ liệu, pipeline ETL, DFD và BI'
    doc.save(DOC_OUT)
    print(DOC_OUT)

if __name__=='__main__': main()
