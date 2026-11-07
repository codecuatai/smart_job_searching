from typing import Literal
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator
from services.ai.app.cv_outline import Outline


class CustomJD(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    text: str = Field(min_length=20, max_length=20000)
    sourceUrl: str = Field(default='', max_length=2000, pattern=r'^(https?://[^\s]+)?$')
    mustHaveSkills: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode='after')
    def bounded_skills(self):
        if any(not s.strip() or len(s) > 100 for s in self.mustHaveSkills):
            raise ValueError('Kỹ năng bắt buộc tối đa 100 ký tự mỗi mục.')
        from services.ai.app.engine import extract_skills, normalize
        if not set(extract_skills(' '.join(self.mustHaveSkills))) <= set(extract_skills(self.text)):
            raise ValueError('Kỹ năng bắt buộc cần có trong nội dung JD đã dán.')
        if any(not extract_skills(s) and normalize(s) not in normalize(self.text) for s in self.mustHaveSkills):
            raise ValueError('Yêu cầu bắt buộc cần trích từ nội dung JD đã dán.')
        return self


class CreateConsultation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    resumeId: str
    jobId: str | None = None
    customJd: CustomJD | None = None

    @model_validator(mode='after')
    def one_target(self):
        if bool(self.jobId) == bool(self.customJd):
            raise ValueError('Chọn một JD trong hệ thống hoặc nhập một JD riêng.')
        return self


class Checklist(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cvPermission: bool = False
    outlineReviewed: bool = False
    videoSeconds: int | None = Field(default=None, ge=1, le=3600)
    submitted: bool = False
    deadline: date | None = None


class ConsultationEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=1)
    selectedGapIds: list[str] | None = Field(default=None, max_length=80)
    gapAssessments: dict[str, Literal['not-evidenced', 'learning-needed', 'self-declared', 'unknown']] | None = None
    outline: Outline | None = None
    currentOutline: list[str] | None = Field(default=None, max_length=20)
    script: str | None = Field(default=None, max_length=12000)
    checklist: Checklist | None = None


class RevisionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=1)
