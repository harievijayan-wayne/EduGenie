import json
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, QuestionHistory, Progress
from backend.schemas import QARequest, QAResponse, ApiResponse
from backend.services.gemini_service import gemini_service
from backend.dependencies import get_current_user
from backend.utils.text_utils import format_structured_response

router = APIRouter(prefix="/api/qa", tags=["Question Answering"])

@router.post("", response_model=ApiResponse[QAResponse])
def answer_question(
    request: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Academic Question Answering:
    - Step-by-step clear explanations
    - High-yield key points
    - Concrete examples
    - Safe uncertainty acknowledgment
    """
    system_instruction = (
        "You are EduGenie's Academic Question Answering AI — a brilliant, patient professor.\n"
        "Deliver every answer in a clean, highly structured educational format:\n"
        "1. Heading in bold (`### **Heading Title**`)\n"
        "2. Bullet points with line-by-line explanation (`- **Concept:** detailed line-by-line breakdown`)\n"
        "3. Finally a comprehensive example (`### **Practical Example & Analogy**` with step-by-step points)\n\n"
        "CRITICAL FORMAT RULES:\n"
        "1. ALWAYS use markdown headers: `### **Heading Title**` with empty lines (\\n\\n) before and after.\n"
        "2. Put each point on its own bullet line (`- **Point:** Explanation`). Use double newlines between sections.\n"
        "3. NEVER output a wall of continuous text without line breaks."
    )

    prompt = f"""
Subject: {request.subject}
Target Learner Level: {request.level}
Academic Question: {request.question}

Deliver the answer in this EXACT structured layout:

### **1. Introduction & Overview**
- **Welcome & Definition:** Clear, plain-English definition introducing the core subject.
- **Why It Matters:** Real-world importance and applications.

### **2. Line-by-Line Detailed Explanation**
- **Underlying Principle:** Line-by-line breakdown of how it works.
- **Key Concepts & Rules:** Important laws, properties, or algorithms.
- **Internal Mechanisms:** Step-by-step technical explanation.

### **3. Key Insights & Common Mistakes**
- **Core Insight:** The crucial rule or mental model to remember.
- **Common Trap:** Frequent errors students make and how to avoid them.

### **4. Concrete Step-by-Step Example**
- **Real-World Analogy:** A vivid everyday scenario explaining the intuition.
- **Worked Technical Example:** Concrete step-by-step walkthrough with clear steps and final result.

### **5. Exam Tip & Takeaway**
- **Exam Strategy:** What examiners expect in an answer.

Return ONLY valid JSON matching this schema:
{{
    "answer": "Full elaborative answer using the structure above with ### **Headings**, line-by-line bullet points (- **Bold:**), and worked examples. Must use double newlines between sections.",
    "key_points": [
        "Most critical fundamental takeaway",
        "Core formula, rule, or mechanism with brief explanation",
        "Important edge case or nuance to remember",
        "Real-world application insight",
        "Exam-focused tip or common trap"
    ],
    "examples": [
        "Real-world analogy: detailed everyday example explaining the concept intuitively",
        "Technical example: fully worked step-by-step problem or code walkthrough"
    ]
}}
"""
    result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

    raw_ans = (
        result.get("answer")
        or result.get("reply")
        or result.get("explanation")
        or result.get("simple_explanation")
        or result.get("content")
        or result.get("response")
        or result.get("text")
        or "Here is the step-by-step breakdown of your question."
    )
    ans_text = format_structured_response(raw_ans)
    key_points = [format_structured_response(p) for p in result.get("key_points", ["Fundamental principle applied", "Consistent state maintained"])]
    examples = [format_structured_response(e) for e in result.get("examples", ["Standard textbook case"])]

    # Persist in QuestionHistory
    qh = QuestionHistory(
        user_id=current_user.id,
        question=request.question,
        subject=request.subject,
        level=request.level,
        answer=ans_text,
        key_points_json=json.dumps(key_points),
        examples_json=json.dumps(examples)
    )
    db.add(qh)

    # Award XP and update progress
    current_user.xp = (current_user.xp or 0) + 15
    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if progress:
        progress.questions_asked = (progress.questions_asked or 0) + 1
    db.commit()

    return ApiResponse(
        success=True,
        message="Answer generated successfully.",
        data=QAResponse(
            answer=ans_text,
            key_points=key_points,
            examples=examples
        )
    )
