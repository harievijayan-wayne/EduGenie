import os
import shutil
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Document, Progress
from backend.schemas import (
    DocumentUploadResponse, DocumentQARequest, DocumentQAResponse,
    SummaryRequest, QuizGenerateRequest, NotesGenerateRequest, FlashcardGenerateRequest,
    ApiResponse
)
from backend.services.document_service import document_service
from backend.services.summary_service import summary_service
from backend.services.quiz_service import quiz_service
from backend.services.notes_service import notes_service
from backend.services.flashcard_service import flashcard_service
from backend.services.gemini_service import gemini_service
from backend.dependencies import get_current_user
from backend.utils.validators import validate_uploaded_file
from backend.config import settings

router = APIRouter(prefix="/api/documents", tags=["Documents & RAG"])

@router.post("/upload", response_model=ApiResponse[Dict[str, Any]])
async def upload_document(
    file: UploadFile = File(...),
    action: Optional[str] = Form("analyze"),  # analyze, extract_text, explain
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads PDF, TXT, DOCX or image files (PNG/JPG).
    Extracts text, builds retrieval chunks, and supports multimodal image analysis.
    """
    validate_uploaded_file(file)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = os.path.splitext(file.filename)[1].lower()

    # Image upload handling (multimodal vision)
    if ext in [".png", ".jpg", ".jpeg"]:
        with open(file_path, "rb") as img_file:
            img_bytes = img_file.read()

        multimodal_prompt = (
            "Analyze this educational image (textbook page, diagram, handwritten notes, or exam question). "
            "Explain all diagrams, extract critical formulas/text, solve any questions posed, "
            "and provide 3 practice takeaways."
        )
        analysis_result = gemini_service.generate_multimodal(
            multimodal_prompt,
            img_bytes,
            mime_type=f"image/{ext.replace('.', '')}"
        )

        return ApiResponse(
            success=True,
            message="Image analyzed successfully by EduGenie Multimodal AI.",
            data={
                "type": "image",
                "filename": file.filename,
                "analysis": analysis_result
            }
        )

    # Document upload (PDF, TXT, DOCX)
    doc_record = document_service.process_and_save(file_path, file.filename, current_user.id, db)

    # Extract quick overview topics
    topics = document_service.extract_important_topics(doc_record)
    import json
    doc_record.important_topics_json = json.dumps(topics)
    db.commit()

    current_user.xp = (current_user.xp or 0) + 30
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Document '{file.filename}' processed and indexed for RAG search.",
        data={
            "type": "document",
            "document_id": doc_record.id,
            "filename": doc_record.filename,
            "file_type": doc_record.file_type,
            "chunk_count": doc_record.chunk_count,
            "word_count": len(doc_record.extracted_text.split()),
            "important_topics": topics,
            "preview": doc_record.extracted_text[:400] + ("..." if len(doc_record.extracted_text) > 400 else "")
        }
    )

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all documents uploaded by user."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.uploaded_at.desc()).all()
    import json
    data = [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "chunk_count": d.chunk_count,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else "",
            "topics": json.loads(d.important_topics_json or "[]")
        }
        for d in docs
    ]
    return ApiResponse(success=True, message="Documents retrieved.", data=data)

@router.post("/qa", response_model=ApiResponse[DocumentQAResponse])
def document_qa(
    request: DocumentQARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Answers questions grounded in the uploaded document using vector chunk retrieval (RAG).
    Explicitly reports if the answer is not contained in the document.
    """
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    rag_result = document_service.ask_document_rag(doc, request.question)
    return ApiResponse(
        success=True,
        message="Document query answered using RAG context.",
        data=DocumentQAResponse(**rag_result)
    )

@router.post("/{doc_id}/action", response_model=ApiResponse[Dict[str, Any]])
def document_actions(
    doc_id: int,
    action: str,  # summarize, quiz, notes, flashcards, topics
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Runs high-yield transformations directly from an indexed document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if action == "summarize":
        sum_res = summary_service.summarize(SummaryRequest(content=doc.extracted_text, summary_length="Detailed"))
        return ApiResponse(success=True, message="Document summarized.", data=sum_res.model_dump())
    
    elif action == "quiz":
        q_res = quiz_service.generate_quiz(
            QuizGenerateRequest(topic=f"Material from {doc.filename}", num_questions=5, difficulty="medium"),
            db=db,
            user_id=current_user.id
        )
        return ApiResponse(success=True, message="Quiz generated from document.", data=q_res.model_dump())

    elif action == "notes":
        n_res = notes_service.generate_notes(
            NotesGenerateRequest(topic=doc.filename, note_type="exam", document_id=doc.id),
            db=db,
            user=current_user,
            context_text=doc.extracted_text
        )
        return ApiResponse(success=True, message="Exam notes generated from document.", data=n_res.model_dump())

    elif action == "flashcards":
        fc_res = flashcard_service.generate_flashcards(
            FlashcardGenerateRequest(topic=doc.filename, num_cards=6, document_id=doc.id),
            db=db,
            user=current_user,
            context_text=doc.extracted_text
        )
        return ApiResponse(success=True, message="Flashcards generated from document.", data=fc_res.model_dump())

    elif action == "topics":
        topics = document_service.extract_important_topics(doc)
        return ApiResponse(success=True, message="Topics extracted from document.", data={"topics": topics})

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown action '{action}'")
