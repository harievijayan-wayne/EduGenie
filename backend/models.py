from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    xp = Column(Integer, default=50)
    streak = Column(Integer, default=1)
    level = Column(String(50), default="Novice Scholar")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    question_histories = relationship("QuestionHistory", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    badges = relationship("Badge", back_populates="user", cascade="all, delete-orphan")
    tutor_conversations = relationship("TutorConversation", back_populates="user", cascade="all, delete-orphan")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(50), default="medium")
    total_questions = Column(Integer, default=5)
    questions_json = Column(Text, nullable=False)  # Stores questions, options, explanations
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=5)
    percentage = Column(Float, default=0.0)
    weak_topics_json = Column(Text, default="[]")
    answers_review_json = Column(Text, default="[]")
    completed_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")


class QuestionHistory(Base):
    __tablename__ = "question_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    question = Column(Text, nullable=False)
    subject = Column(String(100), default="General")
    level = Column(String(50), default="intermediate")
    answer = Column(Text, nullable=False)
    key_points_json = Column(Text, default="[]")
    examples_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="question_histories")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    extracted_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    important_topics_json = Column(Text, default="[]")
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="documents")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    topic = Column(String(200), nullable=False)
    current_level = Column(String(50), default="Beginner")
    goal = Column(String(255), nullable=False)
    hours_per_day = Column(Float, default=2.0)
    duration = Column(String(100), default="4 Weeks")
    stages_json = Column(Text, nullable=False)  # Beginner -> Fundamentals -> Intermediate -> Advanced -> Projects
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="learning_paths")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    topic = Column(String(200), nullable=False)
    duration_minutes = Column(Integer, default=25)
    session_type = Column(String(50), default="practice")
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="study_sessions")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    document_id = Column(Integer, nullable=True)
    topic = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    difficulty = Column(String(50), default="medium")
    is_known = Column(Boolean, default=False)
    is_difficult = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="flashcards")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    document_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    note_type = Column(String(50), default="detailed")  # short, detailed, exam
    content_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notes")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_study_minutes = Column(Integer, default=120)
    questions_asked = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    flashcards_reviewed = Column(Integer, default=0)
    summaries_generated = Column(Integer, default=0)
    weak_topics_json = Column(Text, default="[]")
    strong_topics_json = Column(Text, default="[]")
    updated_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="progress")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(String(255), nullable=False)
    icon = Column(String(50), default="award")
    earned_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="badges")


class TutorConversation(Base):
    __tablename__ = "tutor_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    topic = Column(String(200), default="General Study")
    history_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="tutor_conversations")
