from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .engine import MATCHING_MODEL, QUESTIONS, evaluate, extract_skills, match
from .gemini import evaluate_interview as gemini_evaluate_interview
from .gemini import extract_skills as gemini_extract_skills
from .gemini import status as gemini_status

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
    return {'status': 'ok', 'engine': MATCHING_MODEL.get('version', 'baseline-v1'), 'llm': gemini_status()}


@app.post('/match')
def matching(body: MatchInput):
    return [dict(id=job['id'], **match(body.profileText, job)) for job in body.jobs]


@app.post('/skills')
def skills(body: TextInput):
    try:
        return {'skills': gemini_extract_skills(body.text), 'method': 'gemini'}
    except Exception:
        return {'skills': extract_skills(body.text), 'method': 'taxonomy-v1'}


@app.get('/interview/questions')
def questions():
    return [{k: q[k] for k in ('id', 'question')} for q in QUESTIONS]


@app.post('/interview/evaluate')
def evaluation(body: AnswerInput):
    question = next((q for q in QUESTIONS if q['id'] == body.questionId), None)
    if question is None:
        raise HTTPException(404, 'Câu hỏi không tồn tại.')
    try:
        return gemini_evaluate_interview(question['question'], body.answer, question['keywords'])
    except Exception:
        return evaluate(body.questionId, body.answer)
