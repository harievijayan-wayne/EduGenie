import os
import json
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
import docx
from sqlalchemy.orm import Session
from backend.models import Document, User
from backend.utils.text_utils import clean_text, chunk_text
from backend.services.gemini_service import gemini_service
from backend.services.embedding_service import embedding_service
from backend.config import settings

class DocumentService:
    def extract_text(self, file_path: str, ext: str) -> str:
        """Extracts plain text from PDF, DOCX, or TXT."""
        text = ""
        ext = ext.lower()
        if ext == ".pdf":
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        elif ext in [".docx", ".doc"]:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        return clean_text(text)

    def process_and_save(self, file_path: str, filename: str, user_id: int, db: Session) -> Document:
        """Extracts text, calculates chunks, extracts initial summary/topics, and saves to database."""
        ext = os.path.splitext(filename)[1].lower()
        extracted_text = self.extract_text(file_path, ext)
        if not extracted_text:
            extracted_text = "No extractable text found in uploaded document."

        chunks = chunk_text(extracted_text, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

        # Quick preview and metadata
        db_doc = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=ext.replace(".", "").upper(),
            extracted_text=extracted_text,
            chunk_count=len(chunks),
            important_topics_json="[]"
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        return db_doc

    def ask_document_rag(self, doc: Document, question: str) -> Dict[str, Any]:
        """
        RAG Pipeline:
        Document -> Chunks -> Cosine Similarity -> Top Context -> Gemini Prompt -> Grounded Answer.
        If context doesn't contain answer, clearly states that it's not found in the uploaded material.
        """
        chunks = chunk_text(doc.extracted_text, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
        
        if not chunks:
            return {
                "question": question,
                "answer": "This document appears empty or without extractable text.",
                "sources_found": False,
                "referenced_chunks": []
            }

        top_matches = embedding_service.retrieve_relevant_chunks(question, chunks, top_k=3)
        context_passages = [m[0] for m in top_matches]
        combined_context = "\n---\n".join(context_passages)

        system_instruction = (
            "You are EduGenie's Document RAG AI Specialist. Answer questions strictly and accurately "
            "based on the provided context passages. If the answer cannot be found in the provided "
            "context, state clearly: 'Based on the uploaded document, this information is not found in the material.'"
        )

        prompt = f"""
Uploaded Document: {doc.filename}
Context Passages from Document:
\"\"\"{combined_context}\"\"\"

Student's Question: {question}

Provide an accurate, well-explained answer based on the context above.
If the information is not in the text, explicitly state that it is not found in the uploaded material.
"""
        answer_text = gemini_service.generate_text(prompt, system_instruction=system_instruction)

        return {
            "question": question,
            "answer": answer_text,
            "sources_found": len(context_passages) > 0,
            "referenced_chunks": context_passages
        }

    def extract_important_topics(self, doc: Document) -> List[str]:
        """Extracts high-yield topics and themes from the document."""
        preview = doc.extracted_text[:10000]
        prompt = f"""
Analyze the following academic document text and list the top 6-8 most important core topics and themes:
\"\"\"{preview}\"\"\"

Return ONLY valid JSON:
{{
    "topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"]
}}
"""
        result = gemini_service.generate_json(prompt)
        topics = result.get("topics", ["Core Fundamental Concepts", "Theoretical Framework", "Applied Problem Solving"])
        return topics

document_service = DocumentService()
