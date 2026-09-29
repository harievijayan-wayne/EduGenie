import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services.gemini_service import gemini_service
from backend.schemas import NotesGenerateRequest, NotesResponse
from backend.models import Note, User

class NotesService:
    def generate_notes(
        self,
        request: NotesGenerateRequest,
        db: Optional[Session] = None,
        user: Optional[User] = None,
        context_text: Optional[str] = None
    ) -> NotesResponse:
        """
        Generates structured academic study notes:
        - Title, Overview, Definitions, Important Concepts, Examples, Exam Points, Quick Revision.
        """
        ref_text = f"\nReference Material:\n\"\"\"{context_text[:9000]}\"\"\"" if context_text else ""
        
        prompt = f"""
Generate structured {request.note_type} academic notes for: "{request.topic}".
{ref_text}

Format the response strictly as valid JSON matching this schema:
{{
    "title": "Comprehensive Notes on {request.topic}",
    "overview": "High-level summary of the domain, core problems it solves, and why it matters.",
    "definitions": [
        {{"term": "Term 1", "definition": "Formal rigorous definition."}},
        {{"term": "Term 2", "definition": "Formal rigorous definition."}}
    ],
    "important_concepts": [
        {{"concept": "Concept 1", "description": "Detailed explanation of mechanics, properties, and constraints."}},
        {{"concept": "Concept 2", "description": "Detailed explanation."}}
    ],
    "examples": [
        "Concrete example illustrating standard workflow or calculation",
        "Edge case or practical implementation example"
    ],
    "exam_points": [
        "Key point likely to be tested in exams",
        "Crucial distinction or comparison to remember",
        "Common derivation or formula highlight"
    ],
    "quick_revision_section": [
        "Rapid 10-second summary axiom 1",
        "Rapid 10-second summary axiom 2",
        "Rapid 10-second summary axiom 3"
    ]
}}
"""
        system_instruction = "You are a distinguished university professor crafting high-scoring study guides and comprehensive lecture notes."
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        response = NotesResponse(
            title=result.get("title", f"Notes on {request.topic}"),
            overview=result.get("overview", "A systematic guide to understanding fundamental principles and applications."),
            definitions=result.get("definitions", [{"term": request.topic, "definition": "Foundational domain subject."}]),
            important_concepts=result.get("important_concepts", [{"concept": "Core Architecture", "description": "Structural mechanics and data flow."}]),
            examples=result.get("examples", ["Standard textbook sample"]),
            exam_points=result.get("exam_points", ["Focus on diagrams and clear definitions"]),
            quick_revision_section=result.get("quick_revision_section", ["Review before entering exam hall"])
        )

        if db and user:
            db_note = Note(
                user_id=user.id,
                document_id=request.document_id,
                title=response.title,
                note_type=request.note_type,
                content_json=json.dumps(response.model_dump())
            )
            db.add(db_note)
            db.commit()

        return response

notes_service = NotesService()
