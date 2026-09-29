from typing import Dict, Any, List
from backend.services.gemini_service import gemini_service
from backend.schemas import SummaryRequest, SummaryResponse

class SummaryService:
    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """
        Synthesizes long reading materials into concise summaries, key points,
        and extracted terminology definitions.
        """
        system_instruction = (
            "You are an expert academic research summarizer and curriculum designer. "
            "Deliver structured, high-signal educational summaries highlighting core concepts."
        )

        length_guide = {
            "short": "Provide a quick 2-3 sentence executive synopsis.",
            "medium": "Provide a comprehensive 1-2 paragraph structured summary.",
            "detailed": "Provide an in-depth multi-section breakdown covering all nuances and methodology."
        }.get(request.summary_length.lower(), "Provide a balanced educational summary.")

        prompt = f"""
Length Requirement: {request.summary_length} ({length_guide})

Content to Summarize:
\"\"\"{request.content[:15000]}\"\"\"

Generate the response in this exact JSON schema:
{{
    "summary": "The distilled summary text here...",
    "key_points": [
        "First high-yield takeaway",
        "Second high-yield takeaway",
        "Third high-yield takeaway",
        "Fourth high-yield takeaway"
    ],
    "important_terms": [
        {{"term": "Keyword 1", "definition": "Brief definition of keyword 1"}},
        {{"term": "Keyword 2", "definition": "Brief definition of keyword 2"}},
        {{"term": "Keyword 3", "definition": "Brief definition of keyword 3"}}
    ]
}}
"""
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        return SummaryResponse(
            summary=result.get("summary", "Summary of the provided text highlighting core themes and axioms."),
            key_points=result.get("key_points", ["Fundamental definitions", "Applied methodologies", "Systematic outcomes"]),
            important_terms=result.get("important_terms", [
                {"term": "Core Concept", "definition": "The foundational principle underpinning the subject."}
            ])
        )

summary_service = SummaryService()
