"""Reproducible family-disjoint synthetic benchmark. Never represents human gold labels."""
import argparse
import csv
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.ai.app import engine

FAMILIES=[
 ('python-api',['Python','SQL','Docker','FastAPI']),('java-api',['Java','Spring Boot','SQL','Kafka']),
 ('react-web',['React','TypeScript','CSS','Next.js']),('data-bi',['Python','SQL','Power BI','Tableau']),
 ('cloud-ops',['AWS','Docker','Kubernetes','Terraform']),('dotnet',['C#','SQL Server','Docker','Testing']),
 ('ml-engineer',['Python','PyTorch','Machine Learning','Docker']),('warehouse',['SQL','dbt','Airflow','Snowflake']),
 ('go-api',['Go','PostgreSQL','Redis','Docker']),('nlp',['Python','NLP','TensorFlow','REST API']),
 ('mobile',['Kotlin','Swift','Git','Testing']),('php-web',['PHP','MySQL','Laravel','Git'])]


def generate():
    out=[]
    for split, indexes in [('train',range(8)),('validation',range(8,10)),('test',range(10,12))]:
        jobs=[]; profiles=[]
        for i in indexes:
            family,skills=FAMILIES[i]
            for version in range(2):
                jobs.append(dict(id=f'{family}-job-{version}',family=family,title=family,
                                 tags=skills,requirements=skills[:2],mustHaveSkills=skills[:2],niceToHaveSkills=skills[2:],
                                 minimumExperienceYears=2,description=f'Build reliable {family} systems and integration tests. Version {version}.'))
            for level in range(4):
                owned=skills if level==2 else skills[:1]+skills[2:3] if level==1 else ['HTML','CSS'] if level==0 else []
                text=' '.join(owned)+f'. {2 if level==2 else 1} years experience. Portfolio {family}.'
                if level==3:
                    text='I do not know '+', '.join(skills)+'. No technical experience.'
                profiles.append(dict(candidateId=f'{family}-candidate-{level}',family=family,profileText=text,level=level))
        for profile in profiles:
            for job in jobs:
                label=profile['level'] if profile['family']==job['family'] and profile['level']<3 else 0
                out.append(dict(id=profile['candidateId']+'__'+job['id'],candidateId=profile['candidateId'],job=job,
                                profileText='',resumeText=profile['profileText'],label=label,split=split,
                                annotationSource='synthetic-family-rule',gold=False))
    return out


def idf_fit(rows):
    docs={r['candidateId']:r.get('resumeText','')+' '+r['profileText'] for r in rows}
    docs.update({r['job']['id']:' '.join(r['job']['tags'])+' '+r['job']['description'] for r in rows})
    counts=Counter(word for text in docs.values() for word in set(re.findall(r'[a-z0-9+#.]{2,}',engine.normalize(text))))
    return {word:round(math.log((1+len(docs))/(1+count))+1,6) for word,count in sorted(counts.items())}


def train(rows,idf):
    names=['coverage','cosineSimilarity','mustHaveCoverage','experienceFit']
    vectors=[[1]+[engine.feature_values(r['profileText'],r['job'],idf,r.get('resumeText',''))[n] for n in names] for r in rows]
    weights=[0.]*(len(names)+1)
    for _ in range(2000):
        gradient=[0.]*len(weights)
        for row,vector in zip(rows,vectors):
            pred=1/(1+math.exp(-max(-30,min(30,sum(w*x for w,x in zip(weights,vector))))))
            for i,value in enumerate(vector):
                gradient[i]+=(pred-row['label']/2)*value/len(rows)
        weights=[w-.3*g for w,g in zip(weights,gradient)]
    return dict(version='hybrid-v3',bias=round(weights[0],6),weights=dict(zip(names,[round(w,6) for w in weights[1:]])),idf=idf,
                dataProvenance='Synthetic family-disjoint benchmark; NOT human-validated recruitment quality',samples=len(rows))


def metrics(rows,model):
    original=engine.MATCHING_MODEL
    engine.MATCHING_MODEL=model
    try:
        scores=[engine.match(r['profileText'],r['job'],r.get('resumeText',''))['matchScore'] for r in rows]
    finally:
        engine.MATCHING_MODEL=original
    predicted=[2 if s>=75 else 1 if s>=35 else 0 for s in scores]
    f1=[]
    for label in range(3):
        tp=sum(p==y==label for p,y in zip(predicted,[r['label'] for r in rows]))
        fp=sum(p==label and r['label']!=label for p,r in zip(predicted,rows))
        fn=sum(p!=label and r['label']==label for p,r in zip(predicted,rows))
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    grouped=defaultdict(list)
    for row,score in zip(rows,scores): grouped[row['candidateId']].append((score,row['label']))
    rankings=[]
    for items in grouped.values():
        relevant=sum(label>0 for _,label in items)
        if not relevant: continue
        top=sorted(items,key=lambda item:item[0],reverse=True)[:5]
        ideal=sorted([label for _,label in items],reverse=True)[:5]
        dcg=sum((2**label-1)/math.log2(i+2) for i,(_,label) in enumerate(top))
        idcg=sum((2**label-1)/math.log2(i+2) for i,label in enumerate(ideal))
        rankings.append((sum(label>0 for _,label in top)/5,sum(label>0 for _,label in top)/relevant,dcg/idcg if idcg else 0))
    return dict(samples=len(rows),accuracy=round(sum(p==r['label'] for p,r in zip(predicted,rows))/len(rows),4),
                macroF1=round(sum(f1)/3,4),precisionAt5=round(sum(v[0] for v in rankings)/len(rankings),4),
                recallAt5=round(sum(v[1] for v in rankings)/len(rankings),4),ndcgAt5=round(sum(v[2] for v in rankings)/len(rankings),4),
                rankingQueryCount=len(rankings),qualityClaim='human-reviewed' if all(r.get('gold') for r in rows) else 'synthetic-only')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gold',type=Path,help='Optional independently reviewed JSONL with split and gold=true.')
    args=parser.parse_args()
    rows=[json.loads(l) for l in args.gold.read_text(encoding='utf-8').splitlines() if l.strip()] if args.gold else generate()
    if args.gold and not all(r.get('gold') and r.get('annotationSource')=='human-reviewed' for r in rows):
        raise SystemExit('Gold evaluation requires independently human-reviewed annotations.')
    groups={name:[r for r in rows if r['split']==name] for name in ('train','validation','test')}
    if any(not group for group in groups.values()) or any(r.get('label') not in (0,1,2) for r in rows):
        raise SystemExit('Every split must have samples and relevance labels 0,1,2.')
    for left,right in [('train','validation'),('train','test'),('validation','test')]:
        for kind in ('candidateId','job'):
            ids=lambda group:{r['job']['id'] if kind=='job' else r[kind] for r in group}
            if ids(groups[left]) & ids(groups[right]): raise SystemExit('Candidate/job leakage between splits.')
    folder=ROOT/'data/evaluation'/('gold-benchmark' if args.gold else 'benchmark')
    folder.mkdir(parents=True,exist_ok=True)
    for name,items in groups.items():
        (folder/f'{name}.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in items)+'\n',encoding='utf-8')
    baseline=json.loads((ROOT/'services/ai/models/matching-v2.json').read_text(encoding='utf-8'))
    candidate=train(groups['train'],idf_fit(groups['train']))
    validation={m:metrics(groups['validation'],model) for m,model in [('baseline-v2',baseline),('candidate-v3',candidate)]}
    selected=validation['candidate-v3']['ndcgAt5']>=validation['baseline-v2']['ndcgAt5'] and validation['candidate-v3']['macroF1']>=validation['baseline-v2']['macroF1']
    candidate['deploymentDecision']='selected on validation only' if selected else 'not selected: validation regression'
    artifact=ROOT/'services/ai/models'/('matching-v3.json' if selected else 'candidate-v3.json')
    artifact.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'services/ai/models/matching-selection.json').write_text(json.dumps(dict(artifact=artifact.name if selected else 'matching-v2.json',basis='validation macro-F1 and NDCG, no test selection'),indent=2)+'\n',encoding='utf-8')
    report=dict(provenance='human-reviewed' if args.gold else 'synthetic-family-rule',goldLabelCount=sum(bool(r.get('gold')) for r in rows),
                samples=len(rows),splits={k:len(v) for k,v in groups.items()},leakageCheck='no shared candidate/job IDs',validation=validation,
                heldOutTest={m:metrics(groups['test'],model) for m,model in [('baseline-v2',baseline),('candidate-v3',candidate)]},
                candidateDeployed=selected,selectionBasis='validation only; never select on held-out test',
                datasetHash=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
    import time
    started=time.perf_counter()
    metrics(groups['test'],baseline)
    report['latencyMsPerPair']=round(1000*(time.perf_counter()-started)/len(groups['test']),3)
    report['ablationTest']={feature:metrics(groups['test'],dict(candidate,weights={k:v for k,v in candidate['weights'].items() if k!=feature})) for feature in candidate['weights']}
    report['scorerVersion']=engine.SCORER_VERSION
    report['inputAblation']={
        'cvOnly':metrics([dict(r,profileText='') for r in groups['test']],baseline),
        'profileOnly':metrics([dict(r,profileText=r.get('resumeText',''),resumeText='') for r in groups['test']],baseline),
        'combined':metrics([dict(r,profileText=r.get('resumeText','')) for r in groups['test']],baseline)}
    report['limitations']=['Synthetic family rules are not independent human relevance judgments.',
        'Only four relevant candidate queries in each synthetic held-out split; ranking estimates are unstable.',
        'Precision@5 divides by 5 even when the synthetic held-out pool contains only four jobs.',
        'No claim of production hiring accuracy or probability.'] if not args.gold else ['Human annotation quality and template/company leakage must be independently audited.']
    previous=engine.MATCHING_MODEL
    errors=[]
    for name,model in [('baseline-v2',baseline),('candidate-v3',candidate)]:
        engine.MATCHING_MODEL=model
        for row in groups['test']:
            score=engine.match(row['profileText'],row['job'],row.get('resumeText',''))['matchScore']
            predicted=2 if score>=75 else 1 if score>=35 else 0
            if predicted!=row['label']: errors.append(dict(model=name,pairId=row['id'],expected=row['label'],predicted=predicted,score=score))
    engine.MATCHING_MODEL=previous
    report['errors']=errors
    (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (folder/'human-label-template.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.writer(handle);writer.writerow(['pair_id','reviewer_1','reviewer_2','adjudicated_label','evidence','split'])
        writer.writerows([[r['id'],'','','','',r['split']] for r in groups['validation']+groups['test']])
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
