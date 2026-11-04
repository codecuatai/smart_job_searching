import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date as Date, time as Time


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Email không hợp lệ.')
        return value


class Register(Login):
    name: str = Field(min_length=2, max_length=120)
    role: Literal['student', 'recruiter']


class Profile(BaseModel):
    university: str = Field(default='', max_length=200)
    major: str = Field(default='', max_length=200)
    year: str = Field(default='', max_length=100)
    gpa: float = Field(default=0, ge=0, le=4)
    targetRole: str = Field(default='', max_length=200)
    skills: list[str] = Field(default_factory=list, max_length=80)
    projectTitle: str = Field(default='', max_length=200)
    projectSummary: str = Field(default='', max_length=5000)
    projectRepo: str = Field(default='', max_length=300)

    @field_validator('skills')
    @classmethod
    def skill_lengths(cls, values):
        if any(len(value) > 100 for value in values):
            raise ValueError('Tên kỹ năng quá dài.')
        return values

    @field_validator('projectRepo')
    @classmethod
    def repo_url(cls, value):
        if value and not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+/?', value):
            raise ValueError('Dùng URL https://github.com/owner/repo.')
        return value


class JobInput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    location: str = Field(min_length=2, max_length=200)
    workType: Literal['Full-time', 'Internship', 'Part-time'] = 'Full-time'
    salary: str = Field(default='Thỏa thuận', max_length=200)
    category: Literal['backend', 'frontend', 'ai', 'devops', 'mobile']
    description: str = Field(min_length=10, max_length=10000)
    requirements: list[str] = Field(min_length=1, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=50)
    benefits: list[str] = Field(default_factory=list, max_length=30)
    projectSubstituteNote: str = Field(default='', max_length=1000)
    astThreshold: int = Field(default=0, ge=0, le=100)

    @field_validator('requirements', 'tags', 'benefits')
    @classmethod
    def bounded_list(cls, values):
        if any(not v.strip() or len(v) > 1000 for v in values):
            raise ValueError('Mỗi mục cần có nội dung, tối đa 1000 ký tự.')
        return values


class ApplyInput(BaseModel):
    jobId: str


class Schedule(BaseModel):
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(pattern=r'^\d{2}:\d{2}$')
    format: str = Field(min_length=2, max_length=300)
    interviewer: str = Field(default='', max_length=120)

    @field_validator('date')
    @classmethod
    def valid_date(cls, value):
        Date.fromisoformat(value)
        return value

    @field_validator('time')
    @classmethod
    def valid_time(cls, value):
        Time.fromisoformat(value)
        return value


class StageInput(BaseModel):
    stage: Literal['submitted', 'reviewing', 'interview', 'offered']
    interviewSchedule: Schedule | None = None

    @model_validator(mode='after')
    def interview_requires_schedule(self):
        if self.stage == 'interview' and self.interviewSchedule is None:
            raise ValueError('Trạng thái phỏng vấn cần có lịch hẹn.')
        return self


class Answer(BaseModel):
    questionId: str
    answer: str = Field(min_length=1, max_length=10000)
