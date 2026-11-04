import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configure styling
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

os.makedirs('docs/diagrams', exist_ok=True)

# -------------------------------------------------------------
# 1. DIAGRAM: STAR SCHEMA (KHO DỮ LIỆU BI)
# -------------------------------------------------------------
def generate_star_schema():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Color definitions
    FACT_HEADER = '#1A365D'      # Deep Navy
    FACT_BG = '#EBF8FF'          # Light Blue
    DIM_HEADER = '#2B6CB0'       # Medium Blue
    DIM_BG = '#F7FAFC'           # Light Gray/White
    BORDER = '#CBD5E0'
    LINE_COLOR = '#4A5568'

    def draw_table(x, y, w, h, title, fields, is_fact=False):
        header_color = FACT_HEADER if is_fact else DIM_HEADER
        bg_color = FACT_BG if is_fact else DIM_BG
        
        # Background box
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", 
                                      facecolor=bg_color, edgecolor=BORDER, linewidth=1.5, zorder=2)
        ax.add_patch(rect)
        
        # Header box
        header_h = 0.55
        header_rect = patches.FancyBboxPatch((x, y + h - header_h), w, header_h, boxstyle="round,pad=0.03", 
                                            facecolor=header_color, edgecolor=header_color, linewidth=1, zorder=3)
        ax.add_patch(header_rect)
        
        # Header text
        ax.text(x + w/2, y + h - header_h/2, title, color='white', weight='bold', 
                fontsize=9.5 if is_fact else 9, ha='center', va='center', zorder=4)
        
        # Fields text
        line_y = y + h - header_h - 0.22
        for f in fields:
            is_pk = '(PK)' in f
            is_fk = '(FK)' in f
            weight = 'bold' if (is_pk or is_fk) else 'normal'
            color = '#C53030' if is_pk else ('#2B6CB0' if is_fk else '#2D3748')
            ax.text(x + 0.15, line_y, f, color=color, weight=weight, fontsize=7.5, va='center', zorder=4)
            line_y -= 0.21

    # Draw Center FACT Table
    fact_fields = [
        "Application_ID (PK)",
        "Student_ID (FK)",
        "Job_ID (FK)",
        "Company_ID (FK)",
        "Time_ID (FK)",
        "Match_Score (0 - 100%)",
        "Application_Status",
        "Response_Time_Days",
        "Interview_Score",
        "Is_Hired_Flag (0/1)"
    ]
    draw_table(4.1, 2.2, 2.8, 2.8, "FACT_APPLICATIONS\n(Bảng Sự Kiện Ứng Tuyển)", fact_fields, is_fact=True)

    # 1. TOP: DIM_COMPANY
    draw_table(4.1, 5.5, 2.8, 1.7, "DIM_COMPANY (Doanh Nghiệp)", [
        "Company_ID (PK)", "Company_Name", "Industry_Type", "Company_Size", "Partnership_Tier"
    ])

    # 2. LEFT TOP: DIM_STUDENT
    draw_table(0.5, 3.8, 2.9, 2.2, "DIM_STUDENT (Sinh Viên)", [
        "Student_ID (PK)", "University_Name", "Major_Faculty", "GPA_Academic_Score",
        "Verified_Projects_Count", "Graduation_Year", "English_Proficiency"
    ])

    # 3. RIGHT TOP: DIM_JOB
    draw_table(7.6, 3.8, 2.9, 2.2, "DIM_JOB (Công Việc / JD)", [
        "Job_ID (PK)", "Company_ID (FK)", "Job_Title (Intern/Fresher)", "Min_Stipend_Salary",
        "Max_Stipend_Salary", "Work_Schedule_Type", "Required_Min_Skills"
    ])

    # 4. LEFT BOTTOM: DIM_SKILL
    draw_table(0.5, 0.8, 2.9, 1.9, "DIM_SKILL (Kỹ Năng & Năng Lực)", [
        "Skill_ID (PK)", "Skill_Name", "Domain_Category", "Is_Hot_Tech_Flag", "Market_Demand_Weight"
    ])

    # 5. RIGHT BOTTOM: DIM_TIME
    draw_table(7.6, 0.8, 2.9, 1.9, "DIM_TIME (Thời Gian / Kỳ Học)", [
        "Time_ID (PK)", "Full_Date", "Day_Of_Week", "Academic_Semester", "Academic_Year"
    ])

    # Connection Lines from Dimensions to FACT Table
    connections = [
        ((5.5, 5.5), (5.5, 5.0)),       # Company -> FACT
        ((3.4, 4.5), (4.1, 4.0)),       # Student -> FACT
        ((7.6, 4.5), (6.9, 4.0)),       # Job -> FACT
        ((3.4, 1.8), (4.1, 2.6)),       # Skill -> FACT
        ((7.6, 1.8), (6.9, 2.6)),       # Time -> FACT
    ]

    for start, end in connections:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color=LINE_COLOR, lw=1.8, 
                                    shrinkA=4, shrinkB=4, mutation_scale=12))

    # Title & Legend
    ax.text(5.5, 7.2, "MÔ HÌNH KHO DỮ LIỆU HÌNH SAO (DATA WAREHOUSE STAR SCHEMA)", 
            color=FACT_HEADER, weight='bold', fontsize=12, ha='center')
    ax.text(5.5, 6.9, "Phục vụ phân tích đa chiều (OLAP) - Tối ưu cho chỉ số đo lường tuyển dụng & đào tạo", 
            color='#718096', fontsize=8.5, ha='center', style='italic')

    plt.tight_layout()
    output_file = 'docs/diagrams/diagram_star_schema.png'
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {output_file}")


# -------------------------------------------------------------
# 2. DIAGRAM: AI HYBRID MATCHING & CAREER GAP ENGINE
# -------------------------------------------------------------
def generate_ai_matching_flow():
    fig, ax = plt.subplots(figsize=(11, 7.8), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.8)
    ax.axis('off')

    # Title
    ax.text(5.5, 7.5, "KIẾN TRÚC THUẬT TOÁN AI MATCHING & CHẨN ĐOÁN HỔNG KỸ NĂNG", 
            color='#1A365D', weight='bold', fontsize=12, ha='center')
    ax.text(5.5, 7.2, "Cơ chế ghép cặp 2 chiều thông minh kết hợp Ngữ nghĩa Vector, Đồ thị Tri thức và Định lượng đồ án", 
            color='#718096', fontsize=8.5, ha='center', style='italic')

    def draw_card(x, y, w, h, title, items, color, border_color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", 
                                      facecolor=color, edgecolor=border_color, linewidth=1.5, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.25, title, color='#1A202C', weight='bold', fontsize=8.5, ha='center', zorder=3)
        ly = y + h - 0.52
        for it in items:
            ax.text(x + 0.12, ly, it, color='#2D3748', fontsize=7.2, zorder=3)
            ly -= 0.19

    # 1. INPUT LEFT: SINH VIÊN
    draw_card(0.4, 4.4, 2.5, 2.4, "HỒ SƠ NĂNG LỰC SINH VIÊN", [
        "• CV (PDF / DOCX layout)",
        "• Đồ án môn học (GitHub/Source)",
        "• Điểm GPA chuyên ngành",
        "• Thời khóa biểu học kỳ",
        "• Chứng chỉ ngoại ngữ (IELTS/TOEIC)"
    ], '#EBF8FF', '#3182CE')

    # 2. INPUT RIGHT: NHÀ TUYỂN DỤNG
    draw_card(8.1, 4.4, 2.5, 2.4, "YÊU CẦU CÔNG VIỆC (JD)", [
        "• Mô tả trách nhiệm & công nghệ",
        "• Kỹ năng Bắt buộc (Must-have)",
        "• Kỹ năng Ưu tiên (Nice-to-have)",
        "• Hình thức: Part-time / Hybrid",
        "• Mức lương / Trợ cấp thực tập"
    ], '#FEFCBF', '#D69E2E')

    # 3. MIDDLE ENGINES (4 TIÊU CHÍ)
    engines = [
        ("1. Semantic Embedding (35%)", "Sentence-Transformers (bge-m3)\nĐộ tương đồng ngữ nghĩa Cosine 768d", 3.4, 5.8, '#E6FFFA', '#319795'),
        ("2. Skill Graph Traversal (35%)", "Neo4j Skill Ontology\nĐộ phủ kỹ năng + Hệ số lan truyền", 3.4, 4.4, '#EDF2F7', '#4A5568'),
        ("3. Đồ Án & Học Thuật (15%)", "Định lượng điểm Đồ án môn học,\nGPA môn cơ sở & Giải thưởng NCKH", 3.4, 3.0, '#FAF5FF', '#805AD5'),
        ("4. Độ Khớp Thời Gian (15%)", "Tự động so khớp thời khóa biểu học\nvới ca làm việc linh hoạt của công ty", 3.4, 1.6, '#FFF5F5', '#E53E3E'),
    ]

    for title, desc, ex, ey, bg, bd in engines:
        rect = patches.FancyBboxPatch((ex, ey), 4.2, 1.05, boxstyle="round,pad=0.03", facecolor=bg, edgecolor=bd, linewidth=1.3, zorder=2)
        ax.add_patch(rect)
        ax.text(ex + 0.2, ey + 0.75, title, color='#1A202C', weight='bold', fontsize=8.2, zorder=3)
        ax.text(ex + 0.2, ey + 0.35, desc, color='#4A5568', fontsize=7.2, zorder=3)

    # Connections from Left and Right to Middle Engines
    ax.annotate("", xy=(3.3, 5.2), xytext=(2.9, 5.5), arrowprops=dict(arrowstyle="-|>", color='#3182CE', lw=1.8))
    ax.annotate("", xy=(7.7, 5.2), xytext=(8.1, 5.5), arrowprops=dict(arrowstyle="-|>", color='#D69E2E', lw=1.8))

    # Converge into Final Match Score
    rect_score = patches.FancyBboxPatch((4.0, 0.25), 3.0, 0.95, boxstyle="round,pad=0.04", facecolor='#1A365D', edgecolor='#2B6CB0', linewidth=1.5, zorder=2)
    ax.add_patch(rect_score)
    ax.text(5.5, 0.8, "TỔNG HỢP: MATCH SCORE (0 - 100%)", color='#63B3ED', weight='bold', fontsize=8.5, ha='center', zorder=3)
    ax.text(5.5, 0.45, "Final_Score = 0.35*Sim + 0.35*Graph + 0.15*Aca + 0.15*Time", color='white', fontsize=7.5, ha='center', zorder=3)

    # Branches from Score
    # Branch A: Top Match >= 85%
    ax.annotate("", xy=(2.0, 1.2), xytext=(4.0, 0.7), arrowprops=dict(arrowstyle="-|>", color='#38A169', lw=1.6))
    rect_a = patches.FancyBboxPatch((0.4, 0.4), 2.5, 1.0, boxstyle="round,pad=0.03", facecolor='#F0FFF4', edgecolor='#38A169', linewidth=1.3, zorder=2)
    ax.add_patch(rect_a)
    ax.text(1.65, 1.1, "MATCH >= 85%: TOP MATCH", color='#22543D', weight='bold', fontsize=7.8, ha='center', zorder=3)
    ax.text(1.65, 0.65, "Tự động đẩy hồ sơ lên đầu HR\nĐề xuất mời phỏng vấn nhanh", color='#276749', fontsize=7.0, ha='center', zorder=3)

    # Branch B: Gap Analysis < 85%
    ax.annotate("", xy=(9.0, 1.2), xytext=(7.0, 0.7), arrowprops=dict(arrowstyle="-|>", color='#DD6B20', lw=1.6))
    rect_b = patches.FancyBboxPatch((8.1, 0.4), 2.5, 1.0, boxstyle="round,pad=0.03", facecolor='#FFFAF0', edgecolor='#DD6B20', linewidth=1.3, zorder=2)
    ax.add_patch(rect_b)
    ax.text(9.35, 1.1, "MATCH 60-84%: SKILL GAP", color='#7B341E', weight='bold', fontsize=7.8, ha='center', zorder=3)
    ax.text(9.35, 0.65, "Chẩn đoán kỹ năng còn thiếu\nKê đơn lộ trình học tập 2 tuần", color='#9C4221', fontsize=7.0, ha='center', zorder=3)

    plt.tight_layout()
    output_file = 'docs/diagrams/diagram_ai_matching_flow.png'
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {output_file}")


# -------------------------------------------------------------
# 3. DIAGRAM: NEO4J SKILL KNOWLEDGE GRAPH (ĐỒ THỊ TRI THỨC)
# -------------------------------------------------------------
def generate_skill_graph():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.axis('off')

    ax.text(5.0, 6.2, "MINH HỌA ĐỒ THỊ TRI THỨC KỸ NĂNG (NEO4J SKILL KNOWLEDGE GRAPH)", 
            color='#1A365D', weight='bold', fontsize=11.5, ha='center')
    ax.text(5.0, 5.9, "Cơ chế hiểu sâu mối quan hệ ngữ nghĩa thay vì so khớp chuỗi ký tự đơn thuần", 
            color='#718096', fontsize=8.5, ha='center', style='italic')

    def draw_node(x, y, text, category, color, border, r=0.45):
        circle = patches.Circle((x, y), r, facecolor=color, edgecolor=border, linewidth=1.5, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, text, color='#1A202C', weight='bold', fontsize=7.5, ha='center', va='center', zorder=4)

    # Nodes
    # Root: CNTT
    draw_node(5.0, 4.8, "Khoa học\nMáy tính", "Root", '#EBF8FF', '#3182CE', r=0.55)
    
    # Sub domains
    draw_node(2.2, 3.6, "Backend\nDev", "Sub", '#E6FFFA', '#319795', r=0.5)
    draw_node(7.8, 3.6, "Data Science\n& AI", "Sub", '#FAF5FF', '#805AD5', r=0.5)

    # Technologies Backend
    draw_node(1.2, 1.8, "Java Core\n& OOP", "Tech", '#EDF2F7', '#4A5568', r=0.45)
    draw_node(2.4, 0.7, "Spring Boot\nFramework", "Tech", '#FEFCBF', '#D69E2E', r=0.45)
    draw_node(3.6, 2.0, "PostgreSQL\n(JPA/RDBMS)", "Tech", '#EDF2F7', '#4A5568', r=0.45)

    # Technologies Data Science
    draw_node(6.4, 2.0, "Machine\nLearning", "Tech", '#EDF2F7', '#4A5568', r=0.45)
    draw_node(7.8, 0.7, "Deep\nLearning", "Tech", '#FEFCBF', '#D69E2E', r=0.45)
    draw_node(8.8, 2.0, "PowerBI /\nTableau", "Tech", '#FED7D7', '#E53E3E', r=0.45)

    # Arrows with relationship labels
    def draw_rel(p1, p2, label, color='#4A5568', style='->'):
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.3, shrinkA=15, shrinkB=15))
        mx, my = (p1[0] + p2[0])/2, (p1[1] + p2[1])/2
        ax.text(mx, my + 0.1, label, color=color, fontsize=6.8, weight='bold', ha='center', 
                bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none', alpha=0.85), zorder=5)

    draw_rel((5.0, 4.8), (2.2, 3.6), "[:SUBCLASS_OF]")
    draw_rel((5.0, 4.8), (7.8, 3.6), "[:SUBCLASS_OF]")

    draw_rel((2.2, 3.6), (1.2, 1.8), "[:REQUIRES]")
    draw_rel((2.2, 3.6), (2.4, 0.7), "[:USES_FRAMEWORK]")
    draw_rel((2.2, 3.6), (3.6, 2.0), "[:REQUIRES_DB]")

    draw_rel((7.8, 3.6), (6.4, 2.0), "[:SUBCLASS_OF]")
    draw_rel((7.8, 3.6), (7.8, 0.7), "[:SUBCLASS_OF]")
    draw_rel((7.8, 3.6), (8.8, 2.0), "[:TOOL_REQUIRED]")

    # Cross relation: Python connects to Machine Learning
    draw_rel((1.2, 1.8), (6.4, 2.0), "[:RELATED_TO (0.85)]", color='#3182CE', style='<->')
    # Cross relation: ML connects to Deep Learning
    draw_rel((6.4, 2.0), (7.8, 0.7), "[:FOUNDATION_FOR]", color='#805AD5', style='->')

    plt.tight_layout()
    output_file = 'docs/diagrams/diagram_skill_graph.png'
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {output_file}")


if __name__ == "__main__":
    generate_star_schema()
    generate_ai_matching_flow()
    generate_skill_graph()
