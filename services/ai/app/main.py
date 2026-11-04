from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .engine import QUESTIONS, evaluate, extract_skills, match

app = FastAPI(title='UniTalent AI', version='1.0.0')


class MatchInput(BaseModel):
    profileText: str = Field(max_length=100000)
    jobs: list[dict] = Field(max_length=500)


class TextInput(BaseModel):
    text: str = Field(max_length=100000)


class AnswerInput(BaseModel):
    questionId: str
    answer: str = Field(min_length=1, max_length=10000)


@app.get('/health')
def health():
    return {'status': 'ok', 'engine': 'offline-nlp-baseline-v1'}


@app.post('/match')
def matching(body: MatchInput):
    return [dict(id=job['id'], **match(body.profileText, job)) for job in body.jobs]


@app.post('/skills')
def skills(body: TextInput):
    return {'skills': extract_skills(body.text)}


@app.get('/interview/questions')
def questions():
    return [{k: q[k] for k in ('id', 'question')} for q in QUESTIONS]


@app.post('/interview/evaluate')
def evaluation(body: AnswerInput):
    try:
        return evaluate(body.questionId, body.answer)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
