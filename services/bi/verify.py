"""Integration checks against a running, quiescent Docker warehouse."""
import json
import os
import sqlite3
import psycopg
from services.config import database_path
from services.api.app.analytics import market_dataset, summarize
from .main import refresh, warehouse, provision_metabase


def counts():
    with warehouse() as connection:
        return {table:connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                for table in ('fact_job','bridge_job_skill','fact_candidate_skill','fact_application_stage','job_observations')}


def main():
    refresh();before=counts();refresh();after=counts()
    assert before==after,(before,after)
    source=sqlite3.connect(f'file:{database_path().as_posix()}?mode=ro',uri=True);source.row_factory=sqlite3.Row
    with warehouse() as target:
        for dataset in ('real','demo','test'):
            jobs,candidates=market_dataset(source,dataset)
            assert target.execute('SELECT COUNT(*) FROM fact_job WHERE dataset=%s',(dataset,)).fetchone()[0]==len(jobs)
            expected=summarize(jobs,candidates)
            sql=dict(target.execute('SELECT skill,candidate_count FROM bi_skill_supply WHERE dataset=%s',(dataset,)).fetchall())
            for skill in expected['marketStats']: assert sql.get(skill['skill'],0)==skill['candidateCount']
            for trend in expected['salaryTrends']:
                actual=target.execute('SELECT salary_median,sample_size FROM bi_salary_monthly WHERE dataset=%s AND month=%s AND currency=%s AND period=%s',(dataset,trend['month'],trend['currency'],trend['period'])).fetchone()
                assert round(actual[0])==trend['median'] and actual[1]==trend['sampleSize']
        columns=[r[0] for r in target.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public'")]
        assert not any(c in columns for c in ('email','phone','name','content','text','profile','answer'))
    with psycopg.connect(host=os.getenv('WAREHOUSE_HOST','warehouse'),dbname='unitalent_analytics',user='bi_reader',password=os.getenv('BI_READER_PASSWORD','Local-BI-Reader-4829')) as reader:
        assert reader.execute("SELECT has_table_privilege(current_user,'bi_quality','SELECT')").fetchone()[0]
        for table in ('fact_job','fact_candidate_skill','fact_application_stage'):
            assert not reader.execute('SELECT has_table_privilege(current_user,%s,\'SELECT,INSERT,UPDATE,DELETE\')',(table,)).fetchone()[0]
    first=provision_metabase();second=provision_metabase();assert first==second
    source.close()
    print(json.dumps(dict(status='passed',counts=after,idempotent=True,sqlParity=True,readOnlyAggregateRole=True,noRawPiiColumns=True,dashboardId=first)))


if __name__=='__main__':main()
