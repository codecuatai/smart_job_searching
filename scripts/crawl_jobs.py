"""Import public job postings from TopCV and ITviec.

This crawler intentionally uses only public sitemaps and public job pages. It
does not log in, solve CAPTCHAs, call private APIs, or bypass anti-bot systems.
Run from the repository root. The default output is a portable JSON file; use
--import-db only after reviewing the exported data.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
import time
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'var' / 'data' / 'crawled-jobs.json'
USER_AGENT = 'UniTalentJobCrawler/1.0 (+local development)'
SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class CrawlError(RuntimeError):
    pass


def clean_text(value: Any) -> str:
    value = html_lib.unescape(str(value or ''))
    value = re.sub(r'<br\s*/?>', '\n', value, flags=re.I)
    value = re.sub(r'</(p|li|div|h[1-6])\s*>', '\n', value, flags=re.I)
    value = re.sub(r'<[^>]+>', ' ', value)
    return re.sub(r'[ \t\r\f\v]+', ' ', value).replace('\n ', '\n').strip()


def json_ld_documents(page: str) -> Iterable[dict[str, Any]]:
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    for raw in re.findall(pattern, page, flags=re.I | re.S):
        try:
            value = json.loads(html_lib.unescape(raw.strip()))
        except json.JSONDecodeError:
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict):
                if item.get('@type') == 'JobPosting':
                    yield item
                for graph_item in item.get('@graph', []):
                    if isinstance(graph_item, dict) and graph_item.get('@type') == 'JobPosting':
                        yield graph_item


def xml_locations(document: str) -> tuple[list[str], list[str]]:
    try:
        root = ET.fromstring(document)
    except ET.ParseError as error:
        raise CrawlError(f'Không đọc được sitemap XML: {error}') from error
    sitemaps = [node.text.strip() for node in root.findall('sm:sitemap/sm:loc', SITEMAP_NS) if node.text]
    urls = [node.text.strip() for node in root.findall('sm:url/sm:loc', SITEMAP_NS) if node.text]
    return sitemaps, urls


class PublicClient:
    def __init__(self, delay: float, timeout: float = 25) -> None:
        self.delay = max(0, delay)
        self.last_request = 0.0
        self.client = httpx.Client(
            headers={'User-Agent': USER_AGENT, 'Accept-Language': 'vi,en;q=0.8'},
            follow_redirects=True,
            timeout=timeout,
        )
        self.robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def close(self) -> None:
        self.client.close()

    def _robot(self, base: str) -> urllib.robotparser.RobotFileParser:
        if base in self.robots:
            return self.robots[base]
        url = base.rstrip('/') + '/robots.txt'
        response = self._get(url, check_robots=False)
        if response.status_code != 200:
            raise CrawlError(f'{base} không trả robots.txt (HTTP {response.status_code}); bỏ qua để an toàn.')
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(url)
        parser.parse(response.text.splitlines())
        self.robots[base] = parser
        return parser

    def _get(self, url: str, check_robots: bool = True) -> httpx.Response:
        parsed = urlparse(url)
        base = f'{parsed.scheme}://{parsed.netloc}'
        if check_robots and not self._robot(base).can_fetch(USER_AGENT, url):
            raise CrawlError(f'robots.txt không cho phép crawl: {url}')
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        response = self.client.get(url)
        self.last_request = time.monotonic()
        if response.status_code in (403, 429):
            raise CrawlError(f'{url} trả HTTP {response.status_code}; không vượt anti-bot/rate limit.')
        response.raise_for_status()
        return response

    def text(self, url: str) -> str:
        return self._get(url).text


def crawl_sitemap(client: PublicClient, url: str, max_sitemaps: int = 1000) -> list[str]:
    pending = [url]
    seen: set[str] = set()
    result: list[str] = []
    while pending and len(seen) < max_sitemaps:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        sitemaps, urls = xml_locations(client.text(current))
        pending.extend(item for item in sitemaps if item not in seen)
        result.extend(urls)
    return list(dict.fromkeys(result))


def first_text(value: Any) -> str:
    if isinstance(value, list):
        return first_text(value[0]) if value else ''
    if isinstance(value, dict):
        return clean_text(value.get('name') or value.get('addressLocality') or value.get('addressRegion'))
    return clean_text(value)


def location_text(value: Any) -> str:
    values: list[str] = []
    for place in value if isinstance(value, list) else [value]:
        if not isinstance(place, dict):
            continue
        address = place.get('address', place)
        if isinstance(address, dict):
            parts = [address.get('addressLocality'), address.get('addressRegion'), address.get('addressCountry')]
            values.append(', '.join(clean_text(part) for part in parts if clean_text(part)))
    return ' | '.join(dict.fromkeys(item for item in values if item))


def salary_text(value: Any) -> str:
    if not isinstance(value, dict):
        return clean_text(value)
    value = value.get('value', value)
    if isinstance(value, dict):
        currency = value.get('currency', '')
        minimum, maximum = value.get('minValue'), value.get('maxValue')
        unit = value.get('unitText', 'MONTH')
        if minimum is not None and maximum is not None:
            return f'{minimum:g} - {maximum:g} {currency}/{unit.lower()}'
        return clean_text(value.get('value'))
    return clean_text(value)


def skills_from(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r'[,;|\n]+', clean_text(value))
    return list(dict.fromkeys(item.strip() for item in raw if item and item.strip()))[:80]


def category_for(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ('android', 'ios', 'flutter', 'mobile', 'react native')):
        return 'mobile'
    if any(word in text for word in ('frontend', 'front-end', 'react', 'vue', 'angular', 'next.js', 'ui/ux')):
        return 'frontend'
    if any(word in text for word in ('devops', 'cloud', 'kubernetes', 'docker', 'terraform', 'sre', 'infrastructure')):
        return 'devops'
    if any(word in text for word in ('data analyst', 'data engineer', 'machine learning', 'ai ', 'bi ', 'analytics', 'pytorch', 'tensorflow')):
        return 'ai'
    return 'backend'


def stable_id(source: str, url: str) -> str:
    digest = hashlib.sha256(url.encode('utf-8')).hexdigest()[:24]
    return f'external-{source}-{digest}'


def normalize_job(source: str, url: str, posting: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    company = first_text(posting.get('hiringOrganization')) or source.upper()
    title = clean_text(posting.get('title')) or 'Việc làm chưa có tiêu đề'
    description = clean_text(posting.get('description'))[:10000]
    tags = skills_from(posting.get('skills'))
    if not tags:
        try:
            from services.ai.app.engine import extract_skills
            tags = extract_skills(f'{title} {description}')
        except Exception:
            tags = []
    combined = f'{title} {description} {" ".join(tags)}'
    benefits = skills_from(posting.get('jobBenefits'))
    location = location_text(posting.get('jobLocation')) or ('Remote' if posting.get('jobLocationType') else 'Không nêu')
    work_type = clean_text(posting.get('employmentType')).upper()
    work_type = {'FULL_TIME': 'Full-time', 'PART_TIME': 'Part-time', 'CONTRACTOR': 'Part-time', 'INTERN': 'Internship'}.get(work_type, 'Full-time')
    requirements = tags or ['Xem mô tả chi tiết từ nguồn tuyển dụng']
    return {
        'id': stable_id(source, url), 'title': title, 'company': company,
        'logoText': ''.join(part[0] for part in company.split()[:3]).upper() or source[:3].upper(),
        'location': location, 'workType': work_type,
        'salary': salary_text(posting.get('baseSalary')) or 'Thỏa thuận',
        'postedAt': clean_text(posting.get('datePosted')) or fetched_at,
        'category': category_for(combined), 'tags': tags, 'matchScore': 0,
        'projectSubstituteNote': '', 'astCleanCodeScore': 0,
        'description': description, 'requirements': requirements, 'benefits': benefits,
        'missingSkills': [], 'isDemo': False,
        'source': source, 'sourceUrl': url, 'sourceId': url.rstrip('/').rsplit('/', 1)[-1],
        'importedAt': fetched_at,
    }


def crawl_source(client: PublicClient, source: str, limit: int) -> list[dict[str, Any]]:
    config = {
        # ITviec publishes the same postings in English and Vietnamese sitemaps.
        # Use the Vietnamese sitemap once to avoid fetching every job twice.
        'itviec': ['https://itviec.com/twinnings_jobs_desc_vn.xml'],
        'topcv': ['https://www.topcv.vn/sitemap.xml'],
    }[source]
    urls: list[str] = []
    for sitemap in config:
        urls.extend(crawl_sitemap(client, sitemap))
    if source == 'topcv':
        urls = [url for url in urls if '/viec-lam/' in url and not url.endswith('/viec-lam')]
    else:
        urls = [url for url in urls if '/it-jobs/' in url or '/viec-lam-it/' in url]
    urls = list(dict.fromkeys(urls))
    if limit > 0:
        urls = urls[:limit]
    jobs: list[dict[str, Any]] = []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for index, url in enumerate(urls, 1):
        try:
            postings = list(json_ld_documents(client.text(url)))
            if postings:
                jobs.append(normalize_job(source, url, postings[0], fetched_at))
            print(f'[{source}] {index}/{len(urls)} {"ok" if postings else "no JobPosting"}: {url}', file=sys.stderr)
        except (httpx.HTTPError, CrawlError) as error:
            print(f'[{source}] bỏ qua {url}: {error}', file=sys.stderr)
    return jobs


def import_db(jobs: list[dict[str, Any]], owner_email: str) -> int:
    from services.api.app.db import init_db
    from services.api.app.job_maintenance import import_jobs
    init_db()
    return import_jobs(jobs, owner_email)['importedJobs']


def main() -> int:
    parser = argparse.ArgumentParser(description='Crawl public job postings from TopCV and ITviec.')
    parser.add_argument('--source', choices=('topcv', 'itviec', 'all'), default='all')
    parser.add_argument('--limit', type=int, default=20, help='Số trang job tối đa mỗi nguồn; 0 = toàn bộ sitemap.')
    parser.add_argument('--delay', type=float, default=1.0, help='Khoảng nghỉ tối thiểu giữa hai request (giây).')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--import-db', action='store_true', help='Ghi job vào SQLite sau khi crawl.')
    parser.add_argument('--owner-email', default='recruitment@vng.com.vn')
    args = parser.parse_args()
    sources = ('topcv', 'itviec') if args.source == 'all' else (args.source,)
    client = PublicClient(args.delay)
    all_jobs: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    try:
        for source in sources:
            try:
                all_jobs.extend(crawl_source(client, source, args.limit))
            except (httpx.HTTPError, CrawlError) as error:
                errors[source] = str(error)
                print(f'[{source}] không crawl được: {error}', file=sys.stderr)
    finally:
        client.close()
    unique = {job['sourceUrl']: job for job in all_jobs}
    payload = {
        'fetchedAt': datetime.now(timezone.utc).isoformat(),
        'sources': list(sources), 'count': len(unique), 'errors': errors,
        'jobs': list(unique.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Do not destroy a previously successful export when a source is temporarily
    # blocked (for example HTTP 403 from an anti-bot layer). A failed crawl must
    # be retried explicitly instead of turning a usable import file into `jobs: []`.
    if unique or not errors or not args.output.exists():
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        print(f'Giữ nguyên file crawl hiện có vì lần chạy này không lấy được dữ liệu: {args.output}', file=sys.stderr)
    if args.import_db and unique:
        print(f'Đã ghi {import_db(list(unique.values()), args.owner_email)} job vào SQLite.', file=sys.stderr)
    print(f'Đã xuất {len(unique)} job vào {args.output}')
    if errors and not unique:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
