"""Versioned extraction, exact evidence and bounded OCR; no external call on upload."""
import hashlib
import io
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from pypdf import PdfReader
from fastapi import HTTPException
from services.ai.app.engine import SKILLS, extract_skills, normalize
from .data_quality import canonical_skill


def evidence_for(skill, text):
    aliases = SKILLS.get(skill, [skill])
    for line in re.split(r'[\n;!?]', text):
        if skill in extract_skills(line):
            if any(normalize(a) in normalize(line) for a in aliases):
                return line.strip()[:700]
    return ''


def local_analysis(text):
    return dict(status='ready' if text.strip() else 'needs-ocr', method='taxonomy-v2',
                schemaVersion=1, skills=[dict(name=s, evidence=evidence_for(s, text)) for s in extract_skills(text)],
                experienceYears=None, experienceEvidence='', education=[], projects=[],
                unknown=['Mức độ thành thạo và kinh nghiệm chưa được xác minh.'],
                textHash=hashlib.sha256(text.encode()).hexdigest())


def verify_analysis(data, text):
    """Reject hallucinated evidence instead of presenting it as extracted fact."""
    verified = []
    for item in data.get('skills', []):
        skill = canonical_skill(item['name'])
        evidence = item.get('evidence', '').strip()
        if evidence and normalize(evidence) in normalize(text) and skill in extract_skills(evidence):
            verified.append(dict(name=skill, evidence=evidence[:700]))
    data['skills'] = list({s['name']: s for s in verified}.values())
    evidence = data.get('experienceEvidence') or ''
    years = data.get('experienceYears')
    supported_years = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:years?|nam)\b',normalize(evidence))
    if not evidence or normalize(evidence) not in normalize(text) or years is None or not any(float(value.replace(',','.')) == years for value in supported_years):
        data['experienceYears'] = None
        data['experienceEvidence'] = ''
    for field in ('education','projects'):
        data[field] = [value for value in data.get(field,[]) if value.strip() and normalize(value) in normalize(text)]
    data.update(schemaVersion=1, status='ready', textHash=hashlib.sha256(text.encode()).hexdigest())
    return data


def ocr_pdf(content, max_pages=3):
    if not shutil.which('pdftoppm') or not shutil.which('tesseract'):
        raise HTTPException(503, 'OCR chưa sẵn sàng. Chạy API bằng Docker để dùng Poppler/Tesseract.')
    pages = len(PdfReader(io.BytesIO(content)).pages)
    with tempfile.TemporaryDirectory(prefix='unitalent-ocr-') as folder:
        root = Path(folder)
        document = root / 'cv.pdf'
        document.write_bytes(content)
        try:
            subprocess.run(['pdftoppm', '-f', '1', '-l', str(min(pages, max_pages)), '-scale-to', '1800', '-png', str(document), str(root/'page')],
                           check=True, timeout=35, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            texts = []
            for page in sorted(root.glob('page-*.png')):
                result = subprocess.run(['tesseract', str(page), 'stdout', '-l', 'eng+vie'], check=True, timeout=20,
                                        capture_output=True, text=True, encoding='utf-8')
                texts.append(result.stdout)
            return '\n'.join(texts)[:60000], pages > max_pages
        except (subprocess.SubprocessError, OSError) as error:
            raise HTTPException(422, 'Không OCR được PDF trong giới hạn thời gian. Thử xuất PDF có lớp chữ.') from error
