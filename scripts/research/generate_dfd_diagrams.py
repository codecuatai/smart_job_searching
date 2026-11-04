import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configure font styling
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

os.makedirs('docs/diagrams', exist_ok=True)

def generate_dfd_diagram():
    """
    Sơ đồ Luồng Dữ Liệu Tổng Thể (Data Flow Diagram - DFD Level 1)
    Hệ Thống Tìm Kiếm Việc Làm Thông Minh Cho Sinh Viên
    """
    fig, ax = plt.subplots(figsize=(16, 10.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10.5)
    ax.axis('off')

    # Color Palette - Professional Tech Architecture
    BG_CANVAS = '#F8FAFC'
    fig.patch.set_facecolor(BG_CANVAS)

    LAYER_BG = '#FFFFFF'
    BORDER_MAIN = '#CBD5E1'
    TEXT_MAIN = '#0F172A'
    TEXT_MUTED = '#64748B'

    COLOR_SRC = '#2563EB'      # Blue - Data Sources
    COLOR_INGEST = '#0891B2'   # Cyan - Ingestion Engine
    COLOR_ETL = '#059669'      # Emerald - Cleansing & Enrichment
    COLOR_STORAGE = '#D97706'  # Amber - Multi-tier Storage
    COLOR_AI = '#7C3AED'       # Purple - AI & Analytics Engine
    COLOR_UI = '#DC2626'       # Rose/Red - Presentation & Delivery

    # Helper: Draw container block
    def draw_container(x, y, w, h, title, color_header):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                      facecolor=LAYER_BG, edgecolor=color_header, linewidth=1.8, zorder=1)
        ax.add_patch(rect)
        # Header banner
        hh = 0.52
        hrect = patches.FancyBboxPatch((x, y + h - hh), w, hh, boxstyle="round,pad=0.02",
                                       facecolor=color_header, edgecolor=color_header, linewidth=1, zorder=2)
        ax.add_patch(hrect)
        ax.text(x + w / 2, y + h - hh / 2, title, color='white', weight='bold',
                fontsize=10.5, ha='center', va='center', zorder=3)

    # Helper: Draw inner process card
    def draw_node(x, y, w, h, title, subtext, badge=None, border_color='#94A3B8'):
        node = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                      facecolor='#F1F5F9', edgecolor=border_color, linewidth=1.2, zorder=3)
        ax.add_patch(node)
        ax.text(x + w / 2, y + h - 0.28, title, color=TEXT_MAIN, weight='bold',
                fontsize=8.5, ha='center', va='center', zorder=4)
        ax.text(x + w / 2, y + 0.35, subtext, color=TEXT_MUTED,
                fontsize=7.2, ha='center', va='center', zorder=4)
        if badge:
            badge_box = patches.FancyBboxPatch((x + 0.1, y + h - 0.28), 0.7, 0.2, boxstyle="round,pad=0.01",
                                               facecolor='#E2E8F0', edgecolor='none', zorder=5)
            ax.add_patch(badge_box)
            ax.text(x + 0.45, y + h - 0.18, badge, color='#334155', fontsize=6, weight='bold', ha='center', va='center', zorder=6)

    # Header Title of Diagram
    ax.text(8.0, 10.0, "SƠ ĐỒ LUỒNG DỮ LIỆU TỔNG THỂ (DATA FLOW DIAGRAM - DFD LEVEL 1)",
            color='#0F172A', weight='bold', fontsize=15, ha='center')
    ax.text(8.0, 9.68, "Hệ Thống Tìm Kiếm Việc Làm Thông Minh & Phân Tích Độ Lệch Kỹ Năng Cho Sinh Viên (UniTalent AI)",
            color='#475569', fontsize=9.5, ha='center', style='italic')

    # -------------------------------------------------------------
    # STAGE 1: NGUỒN DỮ LIỆU ĐẦU VÀO (X: 0.5 - 2.8)
    # -------------------------------------------------------------
    draw_container(0.5, 0.8, 2.3, 8.5, "1. NGUỒN ĐẦU VÀO", COLOR_SRC)
    draw_node(0.65, 7.3, 2.0, 1.1, "External Job APIs", "LinkedIn, Indeed APIs\n(JSON Batch 6h/lần)", "API", COLOR_SRC)
    draw_node(0.65, 5.7, 2.0, 1.1, "Job Web Scraping", "TopCV, VietnamWorks, ITviec\n(HTML/DOM Extraction)", "CRAWL", COLOR_SRC)
    draw_node(0.65, 4.1, 2.0, 1.1, "Hồ Sơ & CV Sinh Viên", "PDF, DOCX, Thông tin cá nhân\n(User Direct Upload)", "USER", COLOR_SRC)
    draw_node(0.65, 2.5, 2.0, 1.1, "GitHub Codebase", "Source code repositories\n(Git Tree & AST commits)", "GIT", COLOR_SRC)
    draw_node(0.65, 0.95, 2.0, 1.1, "Skill Taxonomy DB", "O*NET & ESCO Taxonomy\n(13,800+ IT Skill Entities)", "DICT", COLOR_SRC)

    # -------------------------------------------------------------
    # STAGE 2: THU THẬP & TIẾP NHẬN (X: 3.2 - 5.5)
    # -------------------------------------------------------------
    draw_container(3.2, 0.8, 2.3, 8.5, "2. INGESTION & PIPELINE", COLOR_INGEST)
    draw_node(3.35, 7.3, 2.0, 1.1, "Scheduled Scrapy", "Bộ lập lịch cào dữ liệu định kỳ\n(Rate Limit & Rotating Proxy)", "ETL", COLOR_INGEST)
    draw_node(3.35, 5.7, 2.0, 1.1, "Kafka Event Stream", "Tiếp nhận real-time khi có\nJD mới hoặc CV sinh viên nộp", "MQ", COLOR_INGEST)
    draw_node(3.35, 4.1, 2.0, 1.1, "PDF/Docx Parser Engine", "Trích xuất layout văn bản CV\n(PyPDF2, pdfplumber)", "PARSE", COLOR_INGEST)
    draw_node(3.35, 2.5, 2.0, 1.1, "Git Cloner & Tree Walk", "Clone repo tạm thời & duyệt file\n(GitPython, Temp Staging)", "CLONE", COLOR_INGEST)
    draw_node(3.35, 0.95, 2.0, 1.1, "Ingestion Buffer / S3", "Lưu trữ Raw Data thô trước khi\nchuyển tiếp sang tiền xử lý", "RAW", COLOR_INGEST)

    # -------------------------------------------------------------
    # STAGE 3: LÀM SẠCH & TIỀN XỬ LÝ (X: 5.9 - 8.2)
    # -------------------------------------------------------------
    draw_container(5.9, 0.8, 2.3, 8.5, "3. LÀM SẠCH & CHUẨN HÓA", COLOR_ETL)
    draw_node(6.05, 7.3, 2.0, 1.1, "Anti-Scam Filter", "Lọc tin tuyển dụng độc hại,\nđa cấp, lương ảo, rác mạng", "SECURITY", COLOR_ETL)
    draw_node(6.05, 5.7, 2.0, 1.1, "SimHash Deduplication", "Loại bỏ tin tuyển dụng trùng lặp\n(Hamming distance <= 3)", "DEDUP", COLOR_ETL)
    draw_node(6.05, 4.1, 2.0, 1.1, "Skill NER Extractor", "Nhận diện thực thể kỹ năng\n(SpaCy + ESCO Ontology)", "NLP", COLOR_ETL)
    draw_node(6.05, 2.5, 2.0, 1.1, "AST Codebase Auditor", "Quét cây AST, tính điểm SOLID,\nđộ phức tạp Cyclomatic & đạo văn", "AST", COLOR_ETL)
    draw_node(6.05, 0.95, 2.0, 1.1, "Sentence-BERT Embedder", "Vector hóa JD và CV\nthành vector 768 chiều ngữ nghĩa", "VECTOR", COLOR_ETL)

    # -------------------------------------------------------------
    # STAGE 4: LƯU TRỮ ĐA TẦNG (X: 8.6 - 10.9)
    # -------------------------------------------------------------
    draw_container(8.6, 0.8, 2.3, 8.5, "4. KHO LƯU TRỮ ĐA TẦNG", COLOR_STORAGE)
    draw_node(8.75, 6.7, 2.0, 1.8, "PostgreSQL (OLTP)", "Cơ sở dữ liệu quan hệ giao dịch\n- Tài khoản người dùng\n- Tin tuyển dụng (JD) đã duyệt\n- Trạng thái nộp đơn & Profile\n(Chuẩn ACID, B-Tree Index)", "RDBMS", COLOR_STORAGE)
    draw_node(8.75, 3.8, 2.0, 2.2, "ClickHouse Star Schema\n(Data Warehouse OLAP)", "Kho dữ liệu BI kinh doanh thông minh\n- Fact_Applications\n- Dim_Student, Dim_Job\n- Dim_Company, Dim_Skill, Dim_Time\n(Truy vấn 10M dòng < 50ms)", "DW", COLOR_STORAGE)
    draw_node(8.75, 0.95, 2.0, 2.1, "Qdrant / Milvus (Vector DB)", "Cơ sở dữ liệu Vector chuyên dụng\n- Vector ngữ nghĩa JD\n- Vector kỹ năng sinh viên\n- Chỉ mục HNSW đồ thị tương đồng\n(Cosine Search < 15ms)", "VDB", COLOR_STORAGE)

    # -------------------------------------------------------------
    # STAGE 5: ĐỘNG CƠ AI & PHÂN TÍCH (X: 11.3 - 13.5)
    # -------------------------------------------------------------
    draw_container(11.3, 0.8, 2.2, 8.5, "5. AI & ANALYTICS", COLOR_AI)
    draw_node(11.45, 6.8, 1.9, 1.8, "Hybrid Cosine Matcher", "Thuật toán so khớp đa chiều:\nScore = 0.55*Cosine + 0.30*AST\n+ 0.15*VoiceScore\n(Quy đổi đồ án thay năm KN)", "AI CORE", COLOR_AI)
    draw_node(11.45, 4.3, 1.9, 1.8, "Skill Gap Analyzer", "Bắt bệnh khoảng trống kỹ năng\nSo sánh CV với JD đích\nĐề xuất lộ trình Micro-learning\n(14 ngày bù đắp lỗ hổng)", "GAP", COLOR_AI)
    draw_node(11.45, 1.8, 1.9, 1.8, "BI OLAP Metrics Engine", "Tính toán chỉ số tuyển dụng:\n- Tỷ lệ chuyển đổi phỏng vấn\n- Độ lệch cung cầu IT theo miền\n- Phân bố mức lương thực tế", "BI", COLOR_AI)

    # -------------------------------------------------------------
    # STAGE 6: GIAO DIỆN & TRẢI NGHIỆM (X: 13.9 - 15.6)
    # -------------------------------------------------------------
    draw_container(13.9, 0.8, 1.7, 8.5, "6. NGƯỜI DÙNG", COLOR_UI)
    draw_node(14.05, 5.4, 1.4, 3.3, "CỔNG SINH VIÊN\n(Student Portal)", "• Gợi ý việc làm AI\n• Báo cáo Clean Code AST\n• Voice AI Mock Interview\n• Theo dõi tiến độ Kanban\n• Lộ trình bù đắp kỹ năng", "STUDENT", COLOR_UI)
    draw_node(14.05, 1.2, 1.4, 3.4, "CỔNG DOANH NGHIỆP\n(Recruiter Portal)", "• Phễu ứng viên chuẩn hóa\n• Đăng tin & cam kết đồ án\n• Xem báo cáo thẩm định AST\n• Dashboard BI Star Schema\n• Lên lịch phỏng vấn", "RECRUITER", COLOR_UI)

    # -------------------------------------------------------------
    # FLOW CONNECTIONS (ARROWS) BETWEEN STAGES
    # -------------------------------------------------------------
    arrow_props = dict(arrowstyle="-|>", color='#64748B', lw=1.5, shrinkA=3, shrinkB=3, mutation_scale=10)

    # Stage 1 -> Stage 2
    ax.annotate("", xy=(3.2, 7.85), xytext=(2.8, 7.85), arrowprops=arrow_props)
    ax.annotate("", xy=(3.2, 6.25), xytext=(2.8, 6.25), arrowprops=arrow_props)
    ax.annotate("", xy=(3.2, 4.65), xytext=(2.8, 4.65), arrowprops=arrow_props)
    ax.annotate("", xy=(3.2, 3.05), xytext=(2.8, 3.05), arrowprops=arrow_props)
    ax.annotate("", xy=(3.2, 1.50), xytext=(2.8, 1.50), arrowprops=arrow_props)

    # Stage 2 -> Stage 3
    ax.annotate("", xy=(5.9, 7.85), xytext=(5.5, 7.85), arrowprops=arrow_props)
    ax.annotate("", xy=(5.9, 6.25), xytext=(5.5, 6.25), arrowprops=arrow_props)
    ax.annotate("", xy=(5.9, 4.65), xytext=(5.5, 4.65), arrowprops=arrow_props)
    ax.annotate("", xy=(5.9, 3.05), xytext=(5.5, 3.05), arrowprops=arrow_props)
    ax.annotate("", xy=(5.9, 1.50), xytext=(5.5, 1.50), arrowprops=arrow_props)

    # Stage 3 -> Stage 4
    ax.annotate("", xy=(8.6, 7.6), xytext=(8.2, 7.6), arrowprops=arrow_props)   # Cleaned data -> Postgres
    ax.annotate("", xy=(8.6, 4.9), xytext=(8.2, 5.0), arrowprops=arrow_props)   # Cleaned data -> Star Schema DW
    ax.annotate("", xy=(8.6, 2.0), xytext=(8.2, 1.5), arrowprops=arrow_props)   # S-BERT embeddings -> Vector DB

    # Stage 4 -> Stage 5
    ax.annotate("", xy=(11.3, 7.7), xytext=(10.9, 7.6), arrowprops=arrow_props)  # DB/Vector -> Matcher
    ax.annotate("", xy=(11.3, 5.2), xytext=(10.9, 5.0), arrowprops=arrow_props)  # DW -> Gap Analyzer
    ax.annotate("", xy=(11.3, 2.7), xytext=(10.9, 4.0), arrowprops=arrow_props)  # DW -> BI Analytics Engine

    # Stage 5 -> Stage 6
    ax.annotate("", xy=(13.9, 7.0), xytext=(13.5, 7.5), arrowprops=arrow_props)  # Matcher -> Student
    ax.annotate("", xy=(13.9, 5.8), xytext=(13.5, 5.2), arrowprops=arrow_props)  # Gap Analyzer -> Student
    ax.annotate("", xy=(13.9, 3.5), xytext=(13.5, 7.5), arrowprops=arrow_props)  # Matcher -> Recruiter
    ax.annotate("", xy=(13.9, 2.2), xytext=(13.5, 2.7), arrowprops=arrow_props)  # BI Metrics -> Recruiter

    output_path = 'docs/diagrams/dfd_data_flow_diagram.png'
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300, facecolor=BG_CANVAS)
    plt.close()
    print(f"Generated: {output_path}")

def generate_etl_pipeline_diagram():
    """
    Sơ đồ Chi Tiết Quy Trình Thu Thập, Làm Sạch & Lưu Trữ Dữ Liệu (ETL & Quality Assurance Pipeline)
    """
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    BG_CANVAS = '#F8FAFC'
    fig.patch.set_facecolor(BG_CANVAS)

    # Title
    ax.text(7.0, 7.5, "QUY TRÌNH THU THẬP, LÀM SẠCH VÀ LƯU TRỮ DỮ LIỆU ĐẢM BẢO CHẤT LƯỢNG (ETL PIPELINE)",
            color='#0F172A', weight='bold', fontsize=13, ha='center')
    ax.text(7.0, 7.15, "Chiến lược Ingestion, Kiểm định chất lượng (Data QA), Khử trùng lặp và Vector hóa chuyên sâu",
            color='#64748B', fontsize=9, ha='center', style='italic')

    # 4 Main Columns
    cols = [
        {"x": 0.6, "w": 2.8, "title": "BƯỚC 1: THU THẬP (INGESTION)", "color": "#0284C7"},
        {"x": 3.8, "w": 2.8, "title": "BƯỚC 2: LÀM SẠCH (CLEANSING)", "color": "#059669"},
        {"x": 7.0, "w": 2.8, "title": "BƯỚC 3: CHUẨN HÓA (ENRICHMENT)", "color": "#7C3AED"},
        {"x": 10.2, "w": 3.2, "title": "BƯỚC 4: LƯU TRỮ & CHỈ MỤC", "color": "#EA580C"}
    ]

    for col in cols:
        rect = patches.FancyBboxPatch((col["x"], 0.6), col["w"], 6.2, boxstyle="round,pad=0.03",
                                      facecolor='#FFFFFF', edgecolor=col["color"], linewidth=1.6, zorder=1)
        ax.add_patch(rect)
        hrect = patches.FancyBboxPatch((col["x"], 6.25), col["w"], 0.45, boxstyle="round,pad=0.02",
                                       facecolor=col["color"], edgecolor=col["color"], linewidth=1, zorder=2)
        ax.add_patch(hrect)
        ax.text(col["x"] + col["w"] / 2, 6.47, col["title"], color='white', weight='bold',
                fontsize=8.5, ha='center', va='center', zorder=3)

    # Helper for inner step boxes
    def draw_step_box(x, y, w, h, step_num, title, bullets):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                     facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1, zorder=3)
        ax.add_patch(box)
        # Badge
        badge = patches.Circle((x + 0.28, y + h - 0.28), 0.16, facecolor='#E2E8F0', edgecolor='none', zorder=4)
        ax.add_patch(badge)
        ax.text(x + 0.28, y + h - 0.28, str(step_num), color='#1E293B', weight='bold', fontsize=8, ha='center', va='center', zorder=5)
        ax.text(x + 0.55, y + h - 0.28, title, color='#0F172A', weight='bold', fontsize=8.5, ha='left', va='center', zorder=5)
        
        # Bullets
        by = y + h - 0.58
        for b in bullets:
            ax.text(x + 0.18, by, f"• {b}", color='#475569', fontsize=7.2, ha='left', va='center', zorder=5)
            by -= 0.24

    # Col 1: Ingestion
    draw_step_box(0.75, 4.4, 2.5, 1.6, "1.1", "Thu Thập Đa Nguồn", 
                  ["REST API: LinkedIn & Indeed (6h/lần)", "Web Scrapy: TopCV, VietnamWorks", "Rate limit & Proxy rotation chống chặn IP"])
    draw_step_box(0.75, 2.4, 2.5, 1.7, "1.2", "Tiếp Nhận Thời Gian Thực", 
                  ["Kafka Topic: student_cv_events", "Kafka Topic: job_post_events", "GitHub Webhook khi sinh viên push commit"])
    draw_step_box(0.75, 0.8, 2.5, 1.3, "1.3", "Vùng Đệm Thô (Raw Staging)", 
                  ["Lưu snapshot JSON thô vào S3/MinIO", "Không làm thay đổi cấu trúc gốc"])

    # Col 2: Cleansing
    draw_step_box(3.95, 4.4, 2.5, 1.6, "2.1", "Khử Rác & Tin Độc Hại", 
                  ["Mô hình lọc Anti-scam (đa cấp, lừa đảo)", "Loại bỏ mã HTML, Javascript, CSS rác", "Phát hiện nội dung vi phạm tiêu chuẩn"])
    draw_step_box(3.95, 2.4, 2.5, 1.7, "2.2", "Khử Trùng Lặp (Deduplication)", 
                  ["Tính SimHash / MinHash chữ ký bài đăng", "So sánh khoảng cách Hamming <= 3", "Gộp tin tuyển dụng từ nhiều nguồn về 1"])
    draw_step_box(3.95, 0.8, 2.5, 1.3, "2.3", "Xử Lý Dữ Liệu Rỗng", 
                  ["Quy đổi khoảng lương thiếu theo chuẩn", "Chuẩn hóa định dạng địa điểm (Hà Nội, HCM)", "Loại bỏ bản ghi hỏng không thể parse"])

    # Col 3: Enrichment
    draw_step_box(7.15, 4.4, 2.5, 1.6, "3.1", "Bóc Tách Kỹ Năng (NER)", 
                  ["Mô hình SpaCy Custom Named Entity", "Ánh xạ từ đồng nghĩa sang ESCO/O*NET", "Ví dụ: 'ReactJS, React.js' -> 'React'"])
    draw_step_box(7.15, 2.4, 2.5, 1.7, "3.2", "Thẩm Định AST Codebase", 
                  ["Phân tích Abstract Syntax Tree (Python/JS)", "Đo lường Clean Code, SOLID, Cyclomatic", "Kiểm định chống sao chép đồ án (Plagiarism)"])
    draw_step_box(7.15, 0.8, 2.5, 1.3, "3.3", "Vector Hóa Ngữ Nghĩa", 
                  ["Sử dụng Sentence-BERT (768 chiều)", "Mã hóa toàn bộ JD và CV năng lực", "Tạo embedding vector cho so khớp ngữ nghĩa"])

    # Col 4: Storage & Indexing
    draw_step_box(10.35, 4.4, 2.9, 1.6, "4.1", "CSDL Giao Dịch PostgreSQL", 
                  ["Quản lý User Auth, Quyền hạn, Job status", "B-Tree index trên Job_ID, Student_ID", "Đảm bảo tính toàn vẹn giao dịch ACID"])
    draw_step_box(10.35, 2.4, 2.9, 1.7, "4.2", "CSDL Vector Qdrant / Milvus", 
                  ["Lưu trữ Embedding 768 chiều JD & CV", "Chỉ mục đồ thị HNSW (Hierarchical NSW)", "Truy vấn Top-K Cosine Similarity < 15ms"])
    draw_step_box(10.35, 0.8, 2.9, 1.3, "4.3", "Kho Dữ Liệu BI ClickHouse", 
                  ["Mô hình Star Schema (Fact_Applications)", "Lưu trữ dạng cột Columnar tối ưu phân tích", "Tính toán Dashboard độ lệch kỹ năng tức thì"])

    # Connector Arrows between stages
    arr = dict(arrowstyle="-|>", color='#64748B', lw=1.8, shrinkA=4, shrinkB=4, mutation_scale=12)
    ax.annotate("", xy=(3.8, 5.2), xytext=(3.4, 5.2), arrowprops=arr)
    ax.annotate("", xy=(7.0, 5.2), xytext=(6.6, 5.2), arrowprops=arr)
    ax.annotate("", xy=(10.2, 5.2), xytext=(9.8, 5.2), arrowprops=arr)

    output_path = 'docs/diagrams/diagram_etl_pipeline.png'
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300, facecolor=BG_CANVAS)
    plt.close()
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    generate_dfd_diagram()
    generate_etl_pipeline_diagram()
