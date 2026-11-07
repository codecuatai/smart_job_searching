"""Metric definitions shared with the warehouse. No test/demo data by default."""
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from .data_quality import canonical_skills, classify_origin, normalized_job


def market_dataset(connection, dataset='real', category=None, location=None, source=None, date_from=None, date_to=None, include_candidates=True):
    origins = {(r['entity_type'], r['entity_id']): r['origin'] for r in connection.execute('SELECT * FROM entity_metadata')}
    jobs = []
    for row in connection.execute('SELECT id,data FROM jobs'):
        raw = json.loads(row['data'])
        origin = origins.get(('job', row['id']), classify_origin(raw, row['id']))
        if origin != dataset:
            continue
        job = normalized_job(raw)
        if category and category != 'all' and job['category'] != category:
            continue
        if location and location.lower() not in job['location'].lower():
            continue
        if source and source != 'all' and job['source'] != source:
            continue
        if date_from and (not job['postedDate'] or job['postedDate'] < date_from):
            continue
        if date_to and (not job['postedDate'] or job['postedDate'] > date_to):
            continue
        jobs.append(job)
    # A canonical source URL is the posting identity; not its imported owner.
    jobs = list({j['sourceUrl'] or j['id']: j for j in jobs}.values())
    if not include_candidates:
        return jobs, []
    candidates = []
    for row in connection.execute("SELECT id,email,profile FROM users WHERE role='student'").fetchall():
        profile = json.loads(row['profile'])
        if origins.get(('user', row['id']), classify_origin(profile, row['id'], row['email'])) != dataset:
            continue
        skills = profile.get('skills', [])
        cv = connection.execute('SELECT a.data,a.confirmed FROM resumes r JOIN resume_analysis a ON a.resume_id=r.id WHERE r.user_id=? ORDER BY r.created_at DESC LIMIT 1', (row['id'],)).fetchone()
        if cv and cv['confirmed']:
            skills += [s['name'] for s in json.loads(cv['data'])['skills']]
        candidates.append(dict(id=row['id'], skills=canonical_skills(skills)))
    return jobs, candidates


def summarize(jobs, candidates):
    categories = Counter(j['category'] for j in jobs)
    demand = Counter(s for j in jobs for s in set(j['skills']))
    supply = Counter(s for p in candidates for s in set(p['skills']))
    skills = [dict(skill=s, jobCount=demand[s], candidateCount=supply[s],
                   demandPercentage=round(100*demand[s]/len(jobs)) if jobs else 0,
                   supplyPercentage=round(100*supply[s]/len(candidates)) if candidates else 0)
              for s in sorted(set(demand) | set(supply), key=lambda s: (-demand[s], s))[:20]]
    for item in skills:
        item['shortagePercentage'] = max(0, item['demandPercentage']-item['supplyPercentage'])
    groups = defaultdict(list)
    salary_counts = Counter()
    time_groups = defaultdict(list)
    for job in jobs:
        salary = job['salary']
        salary_counts[salary['status']] += 1
        if salary['status'] == 'parsed' and salary['minimum'] is not None and salary['maximum'] is not None:
            groups[(job['category'], salary['currency'], salary['period'])].append(salary)
            if job['postedDate']:
                time_groups[(job['postedDate'][:7], salary['currency'], salary['period'])].append(salary)
    def stats(key, values):
        mids = sorted((v['minimum']+v['maximum'])/2 for v in values)
        return dict(category=key[0], currency=key[1], period=key[2], sampleSize=len(values),
                    median=round(statistics.median(mids)), minimum=round(min(mids)), maximum=round(max(mids)),
                    averageMinimum=round(statistics.mean(v['minimum'] for v in values)),
                    averageMaximum=round(statistics.mean(v['maximum'] for v in values)))
    salary_groups = [stats(key, values) for key, values in sorted(groups.items())]
    # Preserve the legacy VND/month contract for existing consumers.
    legacy = [dict(category=r['category'], sampleSize=r['sampleSize'], averageMinimumVnd=r['averageMinimum'], averageMaximumVnd=r['averageMaximum'])
              for r in salary_groups if r['currency'] == 'VND' and r['period'] == 'MONTH']
    trends = [dict(month=key[0], currency=key[1], period=key[2], median=round(statistics.median((v['minimum']+v['maximum'])/2 for v in vals)), sampleSize=len(vals))
              for key, vals in sorted(time_groups.items())]
    return dict(totalJobs=len(jobs), totalStudents=len(candidates), marketStats=skills,
                categoryDistribution=[dict(category=k, jobCount=v, percentage=round(v/len(jobs)*100)) for k,v in categories.items()],
                salaryStats=legacy, salaryGroups=salary_groups, salaryTrends=trends,
                dataQuality=dict(salaryStatuses=dict(salary_counts), missingPostedDate=sum(not j['postedDate'] for j in jobs),
                                 salaryCoverage=round(100*salary_counts['parsed']/len(jobs)) if jobs else 0,
                                 missingSkills=sum(not j['skills'] for j in jobs),
                                 possibleDuplicateGroups=sum(v>1 for v in Counter(j['duplicateFingerprint'] for j in jobs).values()),
                                 expiredJobs=sum(j['active'] is False for j in jobs), unknownValidity=sum(j['active'] is None for j in jobs),
                                 bySource=dict(Counter(j['source'] for j in jobs)),
                                 timeBasis='Ngày đăng tin gốc, không thay bằng ngày crawl.', uniqueCandidates=len(candidates)))


def report(connection, user_id, dataset='real', funnel_from=None, funnel_to=None, **filters):
    jobs, candidates = market_dataset(connection, dataset, **filters)
    result = summarize(jobs, candidates)
    condition='j.owner_id=?'
    params=[user_id]
    if funnel_from:
        condition+=' AND substr(a.created_at,1,10)>=?';params.append(funnel_from)
    if funnel_to:
        condition+=' AND substr(a.created_at,1,10)<=?';params.append(funnel_to)
    count = connection.execute('SELECT COUNT(*) FROM applications a JOIN jobs j ON j.id=a.job_id WHERE '+condition,params).fetchone()[0]
    ranks = {'submitted': 0, 'reviewing': 1, 'interview': 2, 'offered': 3}
    maximum_stage = {}
    for row in connection.execute('SELECT e.application_id,e.stage FROM application_stage_events e JOIN applications a ON a.id=e.application_id JOIN jobs j ON j.id=a.job_id WHERE '+condition,params):
        maximum_stage[row['application_id']] = max(maximum_stage.get(row['application_id'], 0), ranks[row['stage']])
    reached = {stage: sum(rank >= value for rank in maximum_stage.values()) for stage, value in ranks.items()}
    funnel, previous = [], count
    for stage, label in [('submitted','Đã nộp'),('reviewing','Đang xem xét'),('interview','Phỏng vấn'),('offered','Đề nghị')]:
        n = count if stage == 'submitted' else reached.get(stage, 0)
        funnel.append(dict(stage=stage,label=label,count=n,reachedPercentage=round(100*n/count) if count else 0,
                           conversionFromPreviousPercentage=round(100*n/previous) if previous else 0))
        previous = n
    return dict(**result, totalApplications=count, hiringFunnel=funnel, dataset=dataset,
                updatedAt=datetime.now(timezone.utc).isoformat(),
                funnelCohort=dict(fromDate=funnel_from,toDate=funnel_to),
                scope=f'Mẫu {dataset}: số ứng viên duy nhất, không đại diện toàn thị trường; funnel riêng theo ngày nộp đơn {funnel_from or "từ đầu"} đến {funnel_to or "hiện tại"}. Filter thị trường không thay đổi cohort ứng tuyển.')
