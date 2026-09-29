from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

T = TypeVar("T")

# Standard Unified API Envelope
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = "Operation successful"
    data: Optional[T] = None
    error: Optional[str] = None

# Authentication Schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    xp: int
    streak: int
    level: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Q&A Schemas
class QARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=5000)
    subject: Optional[str] = "General Science & Tech"
    level: Optional[str] = "intermediate"  # beginner, intermediate, advanced

    @field_validator('question')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip() or len(v.strip()) < 3:
            raise ValueError("Question cannot be empty or solely whitespace.")
        return v.strip()

class QAResponse(BaseModel):
    answer: str
    key_points: List[str] = []
    examples: List[str] = []

# Explanation Schemas
class ExplainRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=1000)
    level: Optional[str] = "beginner"  # beginner, eli5, intermediate, advanced
    language: Optional[str] = "English"  # English, Tamil, Tanglish

class ExplainResponse(BaseModel):
    concept: str
    simple_explanation: str
    example: str
    real_world_example: str
    key_points: List[str] = []
    common_mistakes: List[str] = []

# Summary Schemas
class SummaryRequest(BaseModel):
    content: str = Field(..., min_length=10)
    summary_length: Optional[str] = "Medium"  # Short, Medium, Detailed

class SummaryResponse(BaseModel):
    summary: str
    key_points: List[str] = []
    important_terms: List[Dict[str, str]] = []

# Quiz Schemas
class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    difficulty: Optional[str] = "medium"  # easy, medium, hard
    num_questions: Optional[int] = Field(default=5, ge=3, le=15)

class QuizQuestion(BaseModel):
    id: Optional[int] = None
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: Optional[str] = "medium"
    topic_tag: Optional[str] = "general"

class QuizResponse(BaseModel):
    quiz_id: Optional[int] = None
    topic: str
    difficulty: str
    total_questions: int
    questions: List[QuizQuestion]

class QuizSubmitRequest(BaseModel):
    quiz_id: int
    user_answers: Dict[str, str]  # { "0": "selected option text", ... }

class QuestionReview(BaseModel):
    question: str
    user_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    explanation: str
    topic_tag: str

class QuizEvaluationResponse(BaseModel):
    score: int
    total_questions: int
    percentage: float
    xp_earned: int
    weak_topics: List[str] = []
    reviews: List[QuestionReview] = []

# Learning Path Schemas
class LearningPathRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    current_level: Optional[str] = "Beginner"
    goal: Optional[str] = "Master concepts and build practical projects"
    hours_per_day: Optional[float] = 2.0
    duration: Optional[str] = "4 Weeks"

class StageCheckpoint(BaseModel):
    milestone: str
    assessment_question: str

class LearningStage(BaseModel):
    stage_name: str  # Beginner, Fundamentals, Intermediate, Advanced, Projects, Assessment
    topic: str
    subtopics: List[str] = []
    estimated_time: str
    practice_tasks: List[str] = []
    resources: List[str] = []
    checkpoint: Optional[StageCheckpoint] = None

class LearningPathResponse(BaseModel):
    topic: str
    current_level: str
    goal: str
    estimated_weeks: str
    stages: List[LearningStage]

# Study Plan Schemas
class StudyPlanRequest(BaseModel):
    exam_date: str
    subjects: List[str]
    hours_per_day: float = 3.0
    current_level: str = "Intermediate"

class DailyScheduleItem(BaseModel):
    day: str
    date_label: Optional[str] = ""
    subjects: List[str]
    topics_to_cover: List[str]
    practice_focus: str
    revision_items: List[str]
    break_recommendations: str
    mock_test_scheduled: bool = False

class StudyPlanResponse(BaseModel):
    exam_date: str
    daily_study_hours: float
    study_plan: List[DailyScheduleItem]
    exam_tips: List[str] = []

# Document Schemas
class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_type: str
    page_count: Optional[int] = 1
    total_words: int
    preview: str

class DocumentQARequest(BaseModel):
    document_id: int
    question: str

class DocumentQAResponse(BaseModel):
    question: str
    answer: str
    sources_found: bool = True
    referenced_chunks: List[str] = []

# Flashcard Schemas
class FlashcardGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    num_cards: Optional[int] = 6
    document_id: Optional[int] = None

class FlashcardItem(BaseModel):
    id: Optional[int] = None
    question: str
    answer: str
    hint: Optional[str] = None
    difficulty: Optional[str] = "medium"
    is_known: bool = False
    is_difficult: bool = False

class FlashcardResponse(BaseModel):
    topic: str
    flashcards: List[FlashcardItem]

# Notes Schemas
class NotesGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    note_type: Optional[str] = "detailed"  # short, detailed, exam
    document_id: Optional[int] = None

class NotesResponse(BaseModel):
    title: str
    overview: str
    definitions: List[Dict[str, str]] = []
    important_concepts: List[Dict[str, str]] = []
    examples: List[str] = []
    exam_points: List[str] = []
    quick_revision_section: List[str] = []

# Exam Answer Schemas
class ExamAnswerRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    marks: int = Field(default=5)  # 2, 5, 10, 13, 16

class ExamAnswerResponse(BaseModel):
    topic: str
    marks: int
    structured_answer: Dict[str, Any]
    word_count_estimate: int
    time_management_tip: str

# Tutor Schemas
class TutorChatRequest(BaseModel):
    message: str
    topic: Optional[str] = "Computer Science"
    level: Optional[str] = "intermediate"
    conversation_id: Optional[int] = None
    action: Optional[str] = "chat"  # chat, explain_simpler, give_example, quiz_me, dont_understand

class TutorChatResponse(BaseModel):
    reply: str
    conversation_id: int
    follow_up_questions: List[str] = []
    hints: List[str] = []
    socratic_tip: Optional[str] = None

# Multimodal Image Schemas
class ImageAnalysisRequest(BaseModel):
    prompt_type: str = "explain"  # explain, extract_text, solve, generate_questions
    custom_prompt: Optional[str] = None

# Progress & Dashboard Schemas
class DashboardMetricsResponse(BaseModel):
    user_name: str
    xp: int
    streak: int
    level: str
    total_study_minutes: int
    questions_asked: int
    quizzes_completed: int
    quiz_accuracy: float
    flashcards_reviewed: int
    weak_areas: List[str] = []
    strong_areas: List[str] = []
    recommended_topics: List[str] = []
    weekly_activity: List[Dict[str, Any]] = []
    recent_badges: List[Dict[str, Any]] = []
