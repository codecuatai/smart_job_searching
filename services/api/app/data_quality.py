"""Shared, explicit normalization for OLTP analytics and the read-only data mart."""
import re
import hashlib
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone
from services.ai.app.engine import SKILLS, normalize


def canonical_skill(value):
    key = normalize(str(value).strip())
    for skill, aliases in SKILLS.items():
        if key in {normalize(skill), *[normalize(a) for a in aliases]}:
            return skill
    return str(value).strip()


def canonical_skills(values):
    return sorted({canonical_skill(v) for v in values if str(v).strip()})


def classify_origin(entity, identifier='', email=''):
    if identifier.startswith('demo-') or entity.get('isDemo') or entity.get('demo'):
        return 'demo'
    if email.lower().endswith(('@example.test', '@audit.test')) or str(entity.get('title', '')).startswith('E2E '):
        return 'test'
    return 'real'


def number(token):
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', token):
        return float(token.replace(',', '').replace('.', ''))
    return float(token.replace(',', '.'))


def parse_salary(value):
    text = str(value or '').lower().strip()
    currency = 'USD' if any(t in text for t in ('usd', '$')) else 'VND' if any(t in text for t in ('vnd', 'vnđ', 'đồng', 'triệu', ' tr', 'tr/', '₫')) else None
    period = 'YEAR' if any(t in text for t in ('/year', '/năm', 'per year', 'annually')) else 'HOUR' if any(t in text for t in ('/hour', '/giờ', 'per hour')) else 'MONTH'
    out = dict(minimum=None, maximum=None, currency=currency, period=period, status='unknown', raw=str(value or ''))
    tokens = re.findall(r'\d+(?:[.,]\d+)*', text)
    if not tokens:
        out['status'] = 'negotiable' if any(t in text for t in ('thỏa thuận', 'thoả thuận', 'negotiable', 'competitive')) else 'missing'
        return out
    million = bool(re.search(r'triệu|\btr\b|\bmil(?:lion)?\b|\d\s*m\b', text))
    thousands = bool(re.search(r'\d\s*k\b', text))
    if currency is None:
        # Large Vietnamese-formatted amounts are unambiguous; bare 10-20 is not.
        if million or (not thousands and all(number(n) >= 1_000_000 for n in tokens[:2])):
            currency = 'VND'
        else:
            return out
    values = [number(t) * (1_000_000 if million else 1000 if thousands else 1) for t in tokens[:2]]
    if any(v <= 0 or v > 1_000_000_000_000 for v in values):
        return out
    if currency == 'VND' and period == 'MONTH' and max(values) < 1000:
        return out
    lo, hi = min(values), max(values)
    if len(values) == 1:
        if re.search(r'up to|tới|đến|dưới|tối đa', text):
            lo = None
        elif re.search(r'from|từ|trên|at least', text):
            hi = None
    out.update(minimum=lo, maximum=hi, currency=currency, status='parsed')
    return out


def normalized_job(job):
    salary = parse_salary(job.get('salary'))
    posted = str(job.get('postedAt', ''))[:10]
    try:
        datetime.strptime(posted, '%Y-%m-%d')
    except ValueError:
        posted = None
    expiry = str(job.get('validThrough') or '')[:10]
    try:
        datetime.strptime(expiry,'%Y-%m-%d')
    except ValueError:
        expiry = None
    signature = '|'.join(normalize(str(job.get(k,''))).strip() for k in ('title','company','location'))
    return dict(id=job['id'], title=job.get('title',''), sourceId=job.get('sourceId'),
                duplicateFingerprint=hashlib.sha256(signature.encode()).hexdigest(),
                validThrough=expiry, active=(expiry >= datetime.now(timezone.utc).date().isoformat()) if expiry else None,
                category=job.get('category', 'other'), location=job.get('location', 'Không nêu'),
                skills=canonical_skills(job.get('tags', [])), source=job.get('source', 'internal'),
                sourceUrl=job.get('sourceUrl'), postedDate=posted,
                observedAt=job.get('importedAt') or datetime.now(timezone.utc).isoformat(), salary=salary)


def canonical_url(value):
    parsed=urlsplit(value)
    return urlunsplit((parsed.scheme.lower(),parsed.netloc.lower(),parsed.path.rstrip('/') or '/', '', ''))
