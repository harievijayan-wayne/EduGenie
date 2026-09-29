import json
from typing import Dict, Any
from backend.services.gemini_service import gemini_service
from backend.schemas import ExplainRequest, ExplainResponse
from backend.utils.text_utils import format_structured_response

class ExplanationService:
    def explain_concept(self, request: ExplainRequest) -> ExplainResponse:
        """
        Generates tailored pedagogical explanations:
        - Beginner, ELI5 (Explain Like I'm 5), Intermediate, Advanced
        - English, Tamil, Tanglish
        """
        system_prompt = (
            "You are an empathetic, award-winning academic educator and storyteller.\n"
            "Deliver every explanation in a clean, highly structured format:\n"
            "- Bold headings (`### **Heading Name**`)\n"
            "- Bullet points with line-by-line explanations (`- **Concept:** detailed line-by-line breakdown`)\n"
            "- Step-by-step concrete examples at the end with code/formulas/steps\n"
            "Use empty lines between sections. Never clump text into a single paragraph."
        )

        language_instruction = f"Explain the concept in {request.language}."
        if request.language.lower() == "tanglish":
            language_instruction = (
                "Explain in Tanglish (Tamil written in English script with smooth conversational tone). "
                "Keep technical terms and formulas in standard English."
            )
        elif request.language.lower() == "tamil":
            language_instruction = (
                "Explain in clear, natural Tamil script. Keep English technical words in brackets where useful."
            )

        level_instruction = f"Target learner level: {request.level}."
        if request.level.lower() == "eli5":
            level_instruction = "Target learner level: Explain Like I'm 5 (use playful, ultra-simple real-world analogies)."

        user_prompt = f"""
Topic: {request.topic}
{level_instruction}
{language_instruction}

Provide a COMPREHENSIVE, ELABORATIVE educational explanation formatted with bold headings and line-by-line bullet points.
Return ONLY valid JSON matching this schema:
{{
    "concept": "{request.topic}",
    "simple_explanation": "Introduction and line-by-line breakdown of the concept using bullet points (- **Key Aspect:** explanation). Clear and accessible.",
    "example": "A concrete step-by-step worked textbook or technical walkthrough with clearly numbered steps or bullet points.",
    "real_world_example": "A vivid everyday analogy explained line-by-line with bullet points connecting each part of the analogy to the concept.",
    "key_points": [
        "Core definition restated as a memorable principle",
        "The most important property or rule with a brief why",
        "How this concept connects to other topics in the subject",
        "Common real-world application or industry use case",
        "What makes this tricky and how to avoid that mistake"
    ],
    "common_mistakes": [
        "First common misconception with a clear explanation of why it is wrong",
        "Second exam pitfall with the correct way to think about it",
        "Third edge case students forget and how to handle it"
    ]
}}
"""
        result = gemini_service.generate_json(user_prompt, system_instruction=system_prompt)
        
        return ExplainResponse(
            concept=result.get("concept", request.topic),
            simple_explanation=format_structured_response(
                result.get("simple_explanation")
                or result.get("explanation")
                or result.get("reply")
                or result.get("answer")
                or result.get("content")
                or "A systematic approach to understanding this concept."
            ),
            example=format_structured_response(result.get("example", "Standard algorithmic or scientific scenario.")),
            real_world_example=format_structured_response(result.get("real_world_example", "Everyday computational or physical system.")),
            key_points=[format_structured_response(k) for k in result.get("key_points", [
                "Understand fundamental axioms",
                "Recognize constraints and invariants",
                "Apply structured reasoning"
            ])],
            common_mistakes=[format_structured_response(m) for m in result.get("common_mistakes", [
                "Overlooking boundary or null conditions",
                "Assuming constant time execution indiscriminately"
            ])]
        )

explanation_service = ExplanationService()
