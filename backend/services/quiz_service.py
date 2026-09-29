import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.services.gemini_service import gemini_service
from backend.schemas import (
    QuizGenerateRequest, QuizResponse, QuizQuestion, 
    QuizSubmitRequest, QuizEvaluationResponse, QuestionReview
)
from backend.models import Quiz, QuizAttempt, User, Progress

class QuizService:
    def generate_quiz(self, request: QuizGenerateRequest, db: Optional[Session] = None, user_id: Optional[int] = None) -> QuizResponse:
        """Generates structured MCQ questions with options, correct answer, explanation, and topic tag."""
        prompt = f"""
Create a multiple choice quiz on the topic: "{request.topic}".
Number of questions: {request.num_questions}
Difficulty: {request.difficulty}

Return ONLY valid JSON with this exact schema:
{{
    "questions": [
        {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option B",
            "explanation": "Clear explanation of why this answer is correct and why others are false.",
            "difficulty": "{request.difficulty}",
            "topic_tag": "Specific subtopic or concept name"
        }}
    ]
}}
"""
        system_instruction = "You are a professional university examiner and educator. Ensure distractors are plausible and correct answers are unambiguous."
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        raw_questions = result.get("questions", [])
        if not raw_questions:
            # Fallback if list was empty
            raw_questions = [
                {
                    "question": f"What is a fundamental characteristic of {request.topic}?",
                    "options": ["High efficiency", "High redundancy", "Random execution", "Unbounded latency"],
                    "correct_answer": "High efficiency",
                    "explanation": f"{request.topic} is primarily leveraged for disciplined, efficient problem solving.",
                    "difficulty": request.difficulty,
                    "topic_tag": request.topic
                }
            ]

        quiz_questions: List[QuizQuestion] = []
        for i, q in enumerate(raw_questions):
            quiz_questions.append(QuizQuestion(
                id=i,
                question=q.get("question", f"Question {i+1} on {request.topic}"),
                options=q.get("options", ["Option A", "Option B", "Option C", "Option D"]),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", "Review core fundamentals."),
                difficulty=q.get("difficulty", request.difficulty),
                topic_tag=q.get("topic_tag", request.topic)
            ))

        saved_quiz_id = None
        if db:
            db_quiz = Quiz(
                user_id=user_id,
                topic=request.topic,
                difficulty=request.difficulty,
                total_questions=len(quiz_questions),
                questions_json=json.dumps([q.model_dump() for q in quiz_questions])
            )
            db.add(db_quiz)
            db.commit()
            db.refresh(db_quiz)
            saved_quiz_id = db_quiz.id

        return QuizResponse(
            quiz_id=saved_quiz_id,
            topic=request.topic,
            difficulty=request.difficulty,
            total_questions=len(quiz_questions),
            questions=quiz_questions
        )

    def evaluate_quiz(self, submission: QuizSubmitRequest, db: Session, user: User) -> QuizEvaluationResponse:
        """Evaluates submitted answers, calculates score and percentage, detects weak areas, and updates user XP."""
        quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
        if not quiz:
            # Return graceful default evaluation
            return QuizEvaluationResponse(
                score=0,
                total_questions=0,
                percentage=0.0,
                xp_earned=0,
                weak_topics=[],
                reviews=[]
            )

        stored_questions = json.loads(quiz.questions_json)
        total_questions = len(stored_questions)
        correct_count = 0
        weak_topics: List[str] = []
        reviews: List[QuestionReview] = []

        for idx, q_data in enumerate(stored_questions):
            str_idx = str(idx)
            user_ans = submission.user_answers.get(str_idx, "").strip()
            correct_ans = q_data.get("correct_answer", "").strip()
            topic_tag = q_data.get("topic_tag", quiz.topic)

            is_correct = (user_ans.lower() == correct_ans.lower())
            if is_correct:
                correct_count += 1
            else:
                if topic_tag and topic_tag not in weak_topics:
                    weak_topics.append(topic_tag)

            reviews.append(QuestionReview(
                question=q_data.get("question", ""),
                user_answer=user_ans if user_ans else "Not Answered",
                correct_answer=correct_ans,
                is_correct=is_correct,
                explanation=q_data.get("explanation", ""),
                topic_tag=topic_tag
            ))

        percentage = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0.0
        xp_earned = (correct_count * 20) + 10  # 20 XP per correct + 10 XP completion bonus

        # Record attempt in database
        attempt = QuizAttempt(
            user_id=user.id,
            quiz_id=quiz.id,
            score=correct_count,
            total_questions=total_questions,
            percentage=percentage,
            weak_topics_json=json.dumps(weak_topics),
            answers_review_json=json.dumps([r.model_dump() for r in reviews])
        )
        db.add(attempt)

        # Update User XP and Progress
        user.xp = (user.xp or 0) + xp_earned
        
        progress = db.query(Progress).filter(Progress.user_id == user.id).first()
        if progress:
            progress.quizzes_completed += 1
            current_weaks = json.loads(progress.weak_topics_json or "[]")
            for wt in weak_topics:
                if wt not in current_weaks:
                    current_weaks.append(wt)
            progress.weak_topics_json = json.dumps(current_weaks[:8])  # keep recent top weak areas

        db.commit()

        return QuizEvaluationResponse(
            score=correct_count,
            total_questions=total_questions,
            percentage=percentage,
            xp_earned=xp_earned,
            weak_topics=weak_topics,
            reviews=reviews
        )

quiz_service = QuizService()
