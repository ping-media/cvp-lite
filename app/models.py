from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserProfile(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="User's full name")
    favorite_foods: List[str] = Field(default=[], description="List of user's favorite foods/cuisines")
    dietary_preferences: List[str] = Field(default=[], description="List of dietary preferences/restrictions")

class UserProfileResponse(BaseModel):
    student_id: str
    name: str
    favorite_foods: List[str]
    dietary_preferences: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RecipeResponse(BaseModel):
    user_id: str
    recipe_name: str
    ingredients: List[str]
    instructions: List[str]
    cooking_time: str
    difficulty: str
    servings: int
    serving_size: str
    dietary_tags: List[str]
    nutritional_facts: dict
    image_prompt: str
    image_url: str
    conversation_id: str
    generated_at: datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class UsersListResponse(BaseModel):
    users: List[UserProfileResponse]
    total_count: int

# class ConversationHistoryResponse(BaseModel):
#     conversation_id: str
#     user_id: str
#     recipe_data: Dict[str, Any]
#     timestamp: datetime
#     type: str

# class ConversationSummaryResponse(BaseModel):
#     user_id: str
#     total_conversations: int
#     recent_conversations: List[Dict[str, Any]]
#     popular_recipe_types: List[Dict[str, Any]] 

# Step 0: Profile setup models
class ProfileSetupRequest(BaseModel):
    first_name: str = Field(..., description="Student's first name")
    last_name: str = Field(..., description="Student's last name")
    grade: str = Field(..., description="Grade or class level, e.g., '9', '10', '11', '12'")
    school_name: str = Field(..., description="Name of the school")
    email: str = Field(..., description="Student's email address")
    phone: Optional[str] = Field(None, description="Phone number")
    city: Optional[str] = Field(None, description="City of residence")
    country: Optional[str] = Field(None, description="Country of residence")
    subject_stream: Optional[str] = Field(None, description="Current subject stream, e.g., 'Science', 'Commerce', 'Arts'")
    hobbies_and_passions: List[str] = Field(default_factory=list, description="List of hobbies and passions")
    dream_job: Optional[str] = Field(None, description="Dream job or aspiration")
    future_self_info: Optional[str] = Field(None, description="Short description of future self vision")
    student_id: Optional[str] = Field(None, description="Optional custom student identifier; generated if omitted")

class ProfileSetupResponse(BaseModel):
    student_id: str
    message: str

# CVP Lite user summary models for listing
class CVPUserSummary(BaseModel):
    student_id: str
    name: str
    grade: Optional[str] = None
    school_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    subject_stream: Optional[str] = None
    hobbies_and_passions: List[str] = Field(default_factory=list)
    dream_job: Optional[str] = None
    future_self_info: Optional[str] = None
    # current_step: Optional[int] = None  # Removed step tracking
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CVPUsersListResponse(BaseModel):
    users: List[CVPUserSummary]
    total_count: int

# Step 1: Interest & Strengths Discovery models (Removed AI features)
# class Step1QuestionOption(BaseModel):
#     id: str
#     text: str

# class Step1Question(BaseModel):
#     id: str
#     prompt: str
#     options: List[Step1QuestionOption]
#     scenario: Optional[str] = None
#     tags: Optional[List[str]] = None  # RIASEC / MI hints (optional)

# class Step1QuestionsRequest(BaseModel):
#     student_id: str

# class Step1QuestionsResponse(BaseModel):
#     student_id: str
#     questions: List[Step1Question]
#     message: str

# class Step1Answer(BaseModel):
#     question_id: str
#     option_id: str

# class Step1SubmitRequest(BaseModel):
#     student_id: str
#     answers: List[Step1Answer]

# class Step1Insight(BaseModel):
#     summary: str
#     riasec_scores: Optional[Dict[str, float]] = None
#     mi_scores: Optional[Dict[str, float]] = None
#     top_themes: Optional[List[str]] = None

# class Step1SubmitResponse(BaseModel):
#     student_id: str
#     insights: Step1Insight
#     message: str

# Generic small responses
class DeleteUserResponse(BaseModel):
    student_id: str
    message: str

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
    student_id: str
    page: Optional[int] = 1
    page_size: Optional[int] = 10
    category_id: Optional[str] = None

class QuestionsResponse(BaseModel):
    data: List[Question]
    meta: QuestionsMeta
    links: QuestionsLinks