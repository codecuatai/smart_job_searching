"""Deterministic provider for isolated offline E2E only. Never used as Gemini evidence."""
import json
import re
from .engine import extract_skills


def generate(prompt):
    if 'Phân tích văn bản CV' in prompt:
        text = prompt.split('. CV: ', 1)[-1]
        years = re.search(r'(\d+(?:\.\d+)?) years experience', text)
        return dict(skills=[dict(name=s, evidence=next((line for line in text.splitlines() if s in extract_skills(line)), text)) for s in extract_skills(text)],
                    experienceYears=float(years[1]) if years else None, experienceEvidence=years[0] if years else '', education=[], projects=[], unknown=[])
    if 'cố vấn học tập' in prompt:
        inputs = json.loads(prompt.split('Dữ liệu: ', 1)[1])
        skill = next(iter(inputs['missingSkills']), 'Kiểm thử API')
        return dict(summary='Kế hoạch kiểm thử offline theo kỹ năng còn thiếu.', roadmap=[dict(week=1,timeRange='Tuần 1', focusTitle=skill,
                    milestones=[f'Áp dụng {skill} vào dự án và viết kiểm thử'], curatedResource='Tài liệu chính thức của công nghệ')])
    if 'người hướng dẫn phỏng vấn' in prompt:
        return dict(questions=[dict(topic=topic,question=f'Bạn áp dụng {topic} trong dự án Python thế nào? Hãy nêu ví dụ và cách kiểm thử.', keywords=['test','Python']) for topic in ('api','database','project')])
    if 'trợ lý đánh giá phỏng vấn' in prompt:
        return dict(score=70,matchedConcepts=['test'],suggestedConcepts=['metrics'],feedback='Bổ sung kết quả kiểm thử đo được. Đây là phản hồi fixture cho kiểm thử hệ thống.')
    raise ValueError('Unknown fixture prompt')
