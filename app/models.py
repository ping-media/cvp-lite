from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

# Questions endpoint models
class QuestionOptionTranslation(BaseModel):
    hi: str
    en: str

class QuestionOption(BaseModel):
    id: str
    label: str
    label_translations: QuestionOptionTranslation

class Question(BaseModel):
    id: str
    text: str
    type: str
    options: List[QuestionOption]
    required: bool
    category_id: str
    weight: float
    lang: str
    created_at: str
    order: int

class AssessmentCategory(BaseModel):
    id: str
    name: str
    description: str
    theory: str
    weight: float

class Assessment(BaseModel):
    id: str
    step_type: str
    title: str
    scientific_basis: str
    generated_at: str
    categories: List[AssessmentCategory]

class QuestionsMeta(BaseModel):
    page: int
    page_size: int
    total: int
    assessment: Assessment

class QuestionsLinks(BaseModel):
    self: str
    next: Optional[str] = None
    prev: Optional[str] = None

class QuestionsRequest(BaseModel):
    page: Optional[int] = 1
    page_size: Optional[int] = 10
    category_id: Optional[str] = None

class QuestionsResponse(BaseModel):
    data: List[Question]
    meta: QuestionsMeta
    links: QuestionsLinks