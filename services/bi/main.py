"""Idempotent, anonymized snapshot ETL and Metabase provisioning."""
import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
import psycopg
from services.api.app.analytics import market_dataset
from services.config import database_path


DDL = '''
CREATE TABLE IF NOT EXISTS dim_time (day DATE PRIMARY KEY, month TEXT NOT NULL, year INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS fact_job (
 id TEXT PRIMARY KEY, dataset TEXT NOT NULL, category TEXT NOT NULL, location TEXT NOT NULL,
 source TEXT NOT NULL, posted_date DATE, observed_at TIMESTAMPTZ NOT NULL,
 salary_min DOUBLE PRECISION,salary_max DOUBLE PRECISION,currency TEXT,period TEXT,salary_status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS bridge_job_skill (job_id TEXT NOT NULL REFERENCES fact_job(id) ON DELETE CASCADE,skill TEXT NOT NULL,PRIMARY KEY(job_id,skill));
CREATE TABLE IF NOT EXISTS fact_candidate_skill (candidate_key TEXT NOT NULL,dataset TEXT NOT NULL,skill TEXT NOT NULL,PRIMARY KEY(candidate_key,skill));
CREATE TABLE IF NOT EXISTS fact_application_stage (application_key TEXT NOT NULL,dataset TEXT NOT NULL,stage TEXT NOT NULL,event_at TIMESTAMPTZ NOT NULL,PRIMARY KEY(application_key,stage));
CREATE TABLE IF NOT EXISTS job_observations (job_id TEXT NOT NULL,day DATE NOT NULL,salary_min DOUBLE PRECISION,salary_max DOUBLE PRECISION,currency TEXT,period TEXT,PRIMARY KEY(job_id,day));
CREATE TABLE IF NOT EXISTS refresh_status (id INTEGER PRIMARY KEY,refreshed_at TIMESTAMPTZ NOT NULL,job_count INTEGER NOT NULL,candidate_count INTEGER NOT NULL);
CREATE OR REPLACE VIEW bi_skill_supply AS SELECT dataset,skill,COUNT(DISTINCT candidate_key) candidate_count FROM fact_candidate_skill GROUP BY dataset,skill;
CREATE OR REPLACE VIEW bi_skill_demand AS SELECT j.dataset,s.skill,COUNT(DISTINCT j.id) job_count FROM fact_job j JOIN bridge_job_skill s ON s.job_id=j.id GROUP BY j.dataset,s.skill;
CREATE OR REPLACE VIEW bi_salary_trend AS SELECT dataset,to_char(posted_date,'YYYY-MM') AS month,category,location,source,currency,period,COUNT(*) sample_size,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2) salary_median
 FROM fact_job WHERE salary_status='parsed' AND salary_min IS NOT NULL AND salary_max IS NOT NULL AND posted_date IS NOT NULL
 GROUP BY dataset,to_char(posted_date,'YYYY-MM'),category,location,source,currency,period;
CREATE OR REPLACE VIEW bi_hiring_funnel AS SELECT dataset,stage,COUNT(DISTINCT application_key) reached,
 ROUND(100.0*COUNT(DISTINCT application_key)/NULLIF((SELECT COUNT(DISTINCT a.application_key) FROM fact_application_stage a WHERE a.dataset=f.dataset AND a.stage='submitted'),0),1) reached_percent
 FROM fact_application_stage f GROUP BY dataset,stage;
CREATE OR REPLACE VIEW bi_salary_monthly AS SELECT dataset,to_char(posted_date,'YYYY-MM') AS month,currency,period,COUNT(*) sample_size,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2) salary_median
 FROM fact_job WHERE salary_status='parsed' AND salary_min IS NOT NULL AND salary_max IS NOT NULL AND posted_date IS NOT NULL
 GROUP BY dataset,to_char(posted_date,'YYYY-MM'),currency,period;
CREATE OR REPLACE VIEW bi_quality AS SELECT dataset,COUNT(*) job_count,COUNT(*) FILTER (WHERE salary_status='parsed') salary_parsed_count,COUNT(*) FILTER (WHERE posted_date IS NULL) missing_posted_date FROM fact_job GROUP BY dataset;
GRANT USAGE ON SCHEMA public TO bi_reader;
GRANT SELECT ON bi_skill_supply,bi_skill_demand,bi_salary_trend,bi_salary_monthly,bi_hiring_funnel,bi_quality,refresh_status TO bi_reader;
'''


def warehouse():
    return psycopg.connect(host=os.getenv('WAREHOUSE_HOST', 'warehouse'), dbname='unitalent_analytics', user='postgres',
                          password=os.getenv('BI_POSTGRES_PASSWORD', 'LocalWarehouse-4829'), connect_timeout=8)


def anon(identifier):
    return hashlib.sha256(identifier.encode()).hexdigest()


def refresh():
    # SQLite's backup API creates a consistent read snapshot without moving or
    # deleting the live DB and without holding a network transaction on OLTP.
    with tempfile.TemporaryDirectory(prefix='unitalent-etl-') as directory:
        path = Path(directory)/'snapshot.db'
        with sqlite3.connect(f'file:{database_path().as_posix()}?mode=ro', uri=True) as original, sqlite3.connect(path) as snapshot:
            original.backup(snapshot)
        source = sqlite3.connect(path)
        source.row_factory = sqlite3.Row
        stamp = datetime.now(timezone.utc)
        datasets = {name: market_dataset(source, name) for name in ('real','demo','test')}
        with warehouse() as target:
            target.execute('SELECT pg_advisory_xact_lock(841399)')
            target.execute(DDL)
            # Atomic replacement of current facts. Observations remain historical.
            target.execute('DELETE FROM bridge_job_skill; DELETE FROM fact_job; DELETE FROM fact_candidate_skill; DELETE FROM fact_application_stage')
            counts = [0,0]
            for dataset, (jobs, candidates) in datasets.items():
                counts[0] += len(jobs); counts[1] += len(candidates)
                for job in jobs:
                    s=job['salary']
                    target.execute('INSERT INTO fact_job VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (job['id'],dataset,job['category'],job['location'],job['source'],job['postedDate'],stamp,s['minimum'],s['maximum'],s['currency'],s['period'],s['status']))
                    if job['postedDate']:
                        day=job['postedDate']
                        target.execute('INSERT INTO dim_time VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',(day,day[:7],int(day[:4])))
                    for skill in job['skills']:
                        target.execute('INSERT INTO bridge_job_skill VALUES (%s,%s)', (job['id'],skill))
                    target.execute('INSERT INTO job_observations VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(job_id,day) DO UPDATE SET salary_min=excluded.salary_min,salary_max=excluded.salary_max,currency=excluded.currency,period=excluded.period',
                                   (job['id'],stamp.date(),s['minimum'],s['maximum'],s['currency'],s['period']))
                for candidate in candidates:
                    for skill in candidate['skills']:
                        target.execute('INSERT INTO fact_candidate_skill VALUES (%s,%s,%s)', (anon(candidate['id']),dataset,skill))
            rank={'submitted':0,'reviewing':1,'interview':2,'offered':3}
            events={}
            rows=source.execute('SELECT a.id,a.created_at,e.stage,e.created_at event_at,m.origin FROM applications a JOIN application_stage_events e ON e.application_id=a.id LEFT JOIN entity_metadata m ON m.entity_type=\'user\' AND m.entity_id=a.student_id')
            for row in rows:
                item=events.setdefault(row['id'],dict(stage=0,date=row['created_at'],origin=row['origin'] or 'real',dates={}))
                item['stage']=max(item['stage'],rank[row['stage']])
                item['dates'].setdefault(row['stage'],row['event_at'])
            for identifier,item in events.items():
                for stage,index in rank.items():
                    if index <= item['stage']:
                        reached_at=item['dates'].get(stage) or next((item['dates'][s] for s,i in rank.items() if i>index and s in item['dates']),item['date'])
                        target.execute('INSERT INTO fact_application_stage VALUES (%s,%s,%s,%s)',(anon(identifier),item['origin'],stage,reached_at))
            target.execute('INSERT INTO refresh_status VALUES (1,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET refreshed_at=excluded.refreshed_at,job_count=excluded.job_count,candidate_count=excluded.candidate_count',(stamp,*counts))
        source.close()
    return dict(jobs=counts[0],candidates=counts[1],refreshedAt=stamp.isoformat())


def provision_metabase():
    with httpx.Client(base_url=os.getenv('METABASE_INTERNAL_URL','http://metabase:3000'), timeout=90) as client:
        def request(method,path,payload=None):
            response=client.request(method,path,json=payload)
            if not response.is_success:
                raise RuntimeError(f'Metabase {path}: HTTP {response.status_code}: {response.text[:350]}')
            return response.json() if response.content else None
        props=request('GET','/api/session/properties')
        email=os.getenv('BI_ADMIN_EMAIL','bi-admin@unitalent.local')
        password=os.getenv('BI_ADMIN_PASSWORD','Local-BI-Admin-4829!')
        if props.get('setup-token'):
            session=request('POST','/api/setup',dict(token=props['setup-token'], user=dict(email=email,password=password,first_name='UniTalent',last_name='BI'),prefs=dict(site_name='UniTalent BI',site_locale='en')))
        else:
            session=request('POST','/api/session',dict(username=email,password=password))
        client.headers['X-Metabase-Session']=session['id']
        databases=request('GET','/api/database')
        databases=databases.get('data',[]) if isinstance(databases,dict) else databases
        database=next((d for d in databases if d['name']=='UniTalent aggregate warehouse'),None)
        if not database:
            database=request('POST','/api/database',dict(name='UniTalent aggregate warehouse',engine='postgres',details=dict(host='warehouse',port=5432,dbname='unitalent_analytics',user='bi_reader',password=os.getenv('BI_READER_PASSWORD','Local-BI-Reader-4829'),ssl=False)))
        questions=[
          ('Ứng viên theo kỹ năng','bar','SELECT skill, candidate_count FROM bi_skill_supply WHERE dataset={{dataset}} ORDER BY candidate_count DESC'),
          ('Nhu cầu kỹ năng','bar','SELECT skill, job_count FROM bi_skill_demand WHERE dataset={{dataset}} ORDER BY job_count DESC LIMIT 20'),
          ('Lương theo tháng (tách tiền tệ/kỳ)','line',"SELECT month,currency||'/'||period AS series,salary_median,sample_size FROM bi_salary_monthly WHERE dataset={{dataset}} ORDER BY month,currency,period"),
          ('Chuyển đổi tuyển dụng tổng hợp','table',"SELECT stage,reached,reached_percent FROM bi_hiring_funnel WHERE dataset={{dataset}} ORDER BY CASE stage WHEN 'submitted' THEN 0 WHEN 'reviewing' THEN 1 WHEN 'interview' THEN 2 ELSE 3 END"),
          ('Chất lượng dữ liệu','table','SELECT * FROM bi_quality WHERE dataset={{dataset}}'),
          ('Lần đồng bộ gần nhất','table','SELECT refreshed_at,job_count,candidate_count FROM refresh_status')]
        existing=request('GET','/api/card')
        existing=existing.get('data',[]) if isinstance(existing,dict) else existing
        cards=[]
        for name,display,query in questions:
            payload=dict(name='TH3 · '+name,type='question',display=display,visualization_settings={'graph.dimensions':['month','series'],'graph.metrics':['salary_median']} if display=='line' else {},
                         dataset_query=dict(database=database['id'],type='native',native=dict(query=query,**({'template-tags': {'dataset': {'name':'dataset','display-name':'Dataset (real/demo/test)','type':'text','default':'real','required':True}}} if '{{dataset}}' in query else {}))))
            previous=next((c for c in existing if c['name']==payload['name']),None)
            cards.append(request('PUT' if previous else 'POST',f'/api/card/{previous["id"]}' if previous else '/api/card',payload))
        dashboards=request('GET','/api/dashboard')
        dashboards=dashboards.get('data',[]) if isinstance(dashboards,dict) else dashboards
        dashboard=next((d for d in dashboards if d['name']=='TH3 · AI & BI'),None)
        if not dashboard:
            dashboard=request('POST','/api/dashboard',dict(name='TH3 · AI & BI',description='Dữ liệu tổng hợp, không có CV/PII. Chọn dataset trong từng câu hỏi; real mặc định. Lương theo ngày đăng gốc, không suy diễn lịch sử.'))
        current=request('GET',f'/api/dashboard/{dashboard["id"]}')
        existing_cards={c['card_id']:c['id'] for c in current.get('dashcards',[]) if c.get('card_id')}
        request('PUT',f'/api/dashboard/{dashboard["id"]}',dict(dashcards=[dict(id=existing_cards.get(card['id'],-i-1),card_id=card['id'],row=(i//2)*6,col=(i%2)*12,size_x=12,size_y=6,parameter_mappings=[]) for i,card in enumerate(cards)]))
        return dashboard['id']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--skip-metabase',action='store_true')
    args=parser.parse_args()
    provisioned=False
    while True:
        try:
            result=refresh()
            if not args.skip_metabase and not provisioned:
                result['dashboardId']=provision_metabase()
                provisioned=True
            Path('/tmp/bi-ready').touch()
            print(json.dumps(result),flush=True)
        except Exception as error:
            print(f'BI refresh failed: {type(error).__name__}: {str(error)[:400]}',flush=True)
            if not args.watch:
                raise
        if not args.watch:
            return
        time.sleep(int(os.getenv('BI_REFRESH_SECONDS','60')))


if __name__=='__main__':
    main()
