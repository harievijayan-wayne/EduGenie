from typing import Dict, Any
from backend.services.gemini_service import gemini_service
from backend.schemas import ExamAnswerRequest, ExamAnswerResponse

class ExamService:
    def generate_exam_answer(self, request: ExamAnswerRequest) -> ExamAnswerResponse:
        """
        Generates university exam answers tailored specifically for:
        2-mark, 5-mark, 10-mark, 13-mark, and 16-mark grading rubrics.
        Includes structured headings, ASCII/Mermaid diagram text representation,
        estimated word counts, and hall time-management guidance.
        """
        marks = request.marks
        
        # Word count & time allocations based on Indian university / international engineering exam rubrics
        rubric_guides = {
            2: {"words": "50-80 words", "time": "2-3 minutes", "format": "Definition + 2-3 precise bullet points"},
            5: {"words": "200-250 words", "time": "7-8 minutes", "format": "Definition + Core Mechanism + Key Points + Short Diagram/Formula + 2 Applications"},
            10: {"words": "400-500 words", "time": "15 minutes", "format": "Introduction + In-depth Architecture + Block Diagram + Step-by-Step Flow + Pros/Cons + Real-world Use Cases"},
            13: {"words": "600-750 words", "time": "20 minutes", "format": "Complete Essay: Intro + Rigorous Definition + Diagram/Mermaid + Detailed Mechanism + Worked Example + Advantages + Disadvantages + Industrial Applications + Conclusion"},
            16: {"words": "800-1000 words", "time": "25 minutes", "format": "Comprehensive University Master Answer: Complete architectural breakdown, formal diagrams, mathematical proofs/pseudocode, comparative analysis table, trade-offs, and critical conclusion"}
        }

        guide = rubric_guides.get(marks, rubric_guides[5])

        prompt = f"""
Academic Topic/Question: "{request.topic}"
Allocated Marks: {marks} Marks
Target Length: {guide['words']}
Suggested Time: {guide['time']}
Rubric Structure: {guide['format']}

Generate a high-scoring university examination answer strictly in valid JSON format:
{{
    "topic": "{request.topic}",
    "marks": {marks},
    "word_count_estimate": 450,
    "time_management_tip": "Spend no more than {guide['time']} on this question in the exam hall.",
    "structured_answer": {{
        "introduction": "Introductory statement contextualizing the subject...",
        "definition": "Formal, academically precise definition...",
        "diagram_representation": "ASCII block diagram or Mermaid code representing the architectural data flow...",
        "detailed_explanation": [
            "Point 1 with clear bold sub-heading and explanation",
            "Point 2 with clear bold sub-heading and explanation",
            "Point 3 with clear bold sub-heading and explanation"
        ],
        "example_or_derivation": "Concrete numerical or algorithmic worked example showing step-by-step resolution...",
        "advantages": ["Advantage 1", "Advantage 2"],
        "limitations": ["Limitation 1", "Limitation 2"],
        "applications": ["Application 1", "Application 2"],
        "conclusion": "Final wrap-up summary ensuring full marks."
    }}
}}
"""
        system_instruction = (
            "You are a strict, top-tier university chief evaluator and professor. "
            "Structure answers to maximize rubric scoring with clean headings, formulas, and diagrams."
        )
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        structured_ans = result.get("structured_answer", {
            "introduction": f"Overview of {request.topic}",
            "definition": f"{request.topic} is defined as a systematic process.",
            "diagram_representation": "[Input] ---> [Processing Engine] ---> [Optimal Output]",
            "detailed_explanation": ["Clear execution steps", "Mathematical invariants"],
            "advantages": ["High performance", "Robust modularity"],
            "limitations": ["Initial complexity", "Resource constraints"],
            "applications": ["Modern enterprise computing", "Distributed architectures"],
            "conclusion": f"{request.topic} remains an indispensable paradigm."
        })

        # Calculate approximate word count
        text_dump = " ".join([str(v) for v in structured_ans.values()])
        word_count = len(text_dump.split())

        return ExamAnswerResponse(
            topic=request.topic,
            marks=marks,
            structured_answer=structured_ans,
            word_count_estimate=word_count,
            time_management_tip=result.get("time_management_tip", f"Allocate {guide['time']} to score maximum marks.")
        )

exam_service = ExamService()
