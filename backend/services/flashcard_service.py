import json
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.gemini_service import gemini_service
from backend.schemas import FlashcardGenerateRequest, FlashcardResponse, FlashcardItem
from backend.models import Flashcard, User

class FlashcardService:
    def generate_flashcards(
        self,
        request: FlashcardGenerateRequest,
        db: Optional[Session] = None,
        user: Optional[User] = None,
        context_text: Optional[str] = None
    ) -> FlashcardResponse:
        """Generates high-yield study flashcards with Question, Answer, Hint, and Difficulty."""
        context_prompt = f"\nReference Material:\n\"\"\"{context_text[:8000]}\"\"\"" if context_text else ""
        
        prompt = f"""
Generate {request.num_cards} high-yield revision flashcards for the topic: "{request.topic}".
{context_prompt}

Ensure questions test active recall, answers are concise and precise, and hints provide gentle memory triggers.
Return ONLY valid JSON with this exact schema:
{{
    "flashcards": [
        {{
            "question": "Clear, direct question prompting active recall?",
            "answer": "Concise, definitive answer or formula.",
            "hint": "Subtle clue or association.",
            "difficulty": "medium"
        }}
    ]
}}
"""
        system_instruction = "You are a cognitive science specialist designing spaced repetition flashcards for rapid academic retention."
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        cards_data = result.get("flashcards", [])
        if not cards_data:
            cards_data = [
                {
                    "question": f"Define the core concept of {request.topic}.",
                    "answer": f"{request.topic} is a structured domain method solving computational or scientific problems.",
                    "hint": "Think about foundational principles.",
                    "difficulty": "easy"
                }
            ]

        items: List[FlashcardItem] = []
        for i, card in enumerate(cards_data):
            saved_id = None
            if db and user:
                db_card = Flashcard(
                    user_id=user.id,
                    document_id=request.document_id,
                    topic=request.topic,
                    question=card.get("question", ""),
                    answer=card.get("answer", ""),
                    hint=card.get("hint", ""),
                    difficulty=card.get("difficulty", "medium"),
                    is_known=False,
                    is_difficult=False
                )
                db.add(db_card)
                db.commit()
                db.refresh(db_card)
                saved_id = db_card.id

            items.append(FlashcardItem(
                id=saved_id or (i + 1),
                question=card.get("question", ""),
                answer=card.get("answer", ""),
                hint=card.get("hint", ""),
                difficulty=card.get("difficulty", "medium"),
                is_known=False,
                is_difficult=False
            ))

        return FlashcardResponse(
            topic=request.topic,
            flashcards=items
        )

flashcard_service = FlashcardService()
