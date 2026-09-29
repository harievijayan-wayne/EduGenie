import json
from typing import Dict, Any, List
from backend.services.gemini_service import gemini_service
from backend.schemas import (
    LearningPathRequest, LearningPathResponse, LearningStage, StageCheckpoint,
    StudyPlanRequest, StudyPlanResponse, DailyScheduleItem
)

class LearningPathService:
    def generate_learning_path(self, request: LearningPathRequest) -> LearningPathResponse:
        """
        Generates a 6-stage progressive mastery roadmap:
        Beginner -> Fundamentals -> Intermediate -> Advanced -> Projects -> Assessment
        """
        system_instruction = (
            "You are a master academic roadmap architect and curriculum engineer. "
            "Design realistic, highly actionable learning progressions with checkpoints and milestones."
        )

        prompt = f"""
Topic: {request.topic}
Learner Current Level: {request.current_level}
Target Goal: {request.goal}
Available Hours Per Day: {request.hours_per_day}
Duration: {request.duration}

Generate a complete 6-stage roadmap structured strictly as valid JSON:
{{
    "topic": "{request.topic}",
    "current_level": "{request.current_level}",
    "goal": "{request.goal}",
    "estimated_weeks": "{request.duration}",
    "stages": [
        {{
            "stage_name": "Beginner",
            "topic": "Stage 1 Focus",
            "subtopics": ["Subtopic A", "Subtopic B", "Subtopic C"],
            "estimated_time": "1 Week (10 Hours)",
            "practice_tasks": ["Hands-on Task 1", "Hands-on Task 2"],
            "resources": ["Recommended Doc/Book", "Interactive Practice Guide"],
            "checkpoint": {{
                "milestone": "Milestone to achieve",
                "assessment_question": "Conceptual check question"
            }}
        }},
        {{
            "stage_name": "Fundamentals",
            "topic": "Stage 2 Focus",
            "subtopics": ["Subtopic A", "Subtopic B"],
            "estimated_time": "1 Week (10 Hours)",
            "practice_tasks": ["Task 1", "Task 2"],
            "resources": ["Resource 1"],
            "checkpoint": {{"milestone": "Milestone 2", "assessment_question": "Question 2"}}
        }},
        {{
            "stage_name": "Intermediate",
            "topic": "Stage 3 Focus",
            "subtopics": ["Subtopic A", "Subtopic B"],
            "estimated_time": "1-2 Weeks",
            "practice_tasks": ["Task 1", "Task 2"],
            "resources": ["Resource 1"],
            "checkpoint": {{"milestone": "Milestone 3", "assessment_question": "Question 3"}}
        }},
        {{
            "stage_name": "Advanced",
            "topic": "Stage 4 Focus",
            "subtopics": ["Subtopic A", "Subtopic B"],
            "estimated_time": "1 Week",
            "practice_tasks": ["Task 1", "Task 2"],
            "resources": ["Resource 1"],
            "checkpoint": {{"milestone": "Milestone 4", "assessment_question": "Question 4"}}
        }},
        {{
            "stage_name": "Projects",
            "topic": "Capstone Practical Implementation",
            "subtopics": ["Design Specs", "Implementation", "Testing & Deployment"],
            "estimated_time": "1 Week",
            "practice_tasks": ["Build end-to-end working system"],
            "resources": ["GitHub Architecture Templates"],
            "checkpoint": {{"milestone": "Live Project Demo", "assessment_question": "Architecture review"}}
        }},
        {{
            "stage_name": "Assessment",
            "topic": "Final Exam & Mock Defense",
            "subtopics": ["Comprehensive Review", "Timed Mock Test", "Interview Drills"],
            "estimated_time": "3 Days",
            "practice_tasks": ["Complete 50 exam-style problems"],
            "resources": ["Past Exam Papers"],
            "checkpoint": {{"milestone": "Mastery Certification Readiness", "assessment_question": "Final integrative problem"}}
        }}
    ]
}}
"""
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        stages_data = result.get("stages", [])
        stages: List[LearningStage] = []
        for s in stages_data:
            cp_data = s.get("checkpoint") or {}
            checkpoint = StageCheckpoint(
                milestone=cp_data.get("milestone", "Stage Completion"),
                assessment_question=cp_data.get("assessment_question", "Explain core principles of this stage.")
            )
            stages.append(LearningStage(
                stage_name=s.get("stage_name", "Stage"),
                topic=s.get("topic", request.topic),
                subtopics=s.get("subtopics", []),
                estimated_time=s.get("estimated_time", "1 Week"),
                practice_tasks=s.get("practice_tasks", []),
                resources=s.get("resources", []),
                checkpoint=checkpoint
            ))

        return LearningPathResponse(
            topic=result.get("topic", request.topic),
            current_level=result.get("current_level", request.current_level),
            goal=result.get("goal", request.goal),
            estimated_weeks=result.get("estimated_weeks", request.duration),
            stages=stages
        )

    def generate_study_plan(self, request: StudyPlanRequest) -> StudyPlanResponse:
        """Generates a structured daily calendar-like schedule leading up to target exam date."""
        subjects_str = ", ".join(request.subjects)
        prompt = f"""
Exam Target Date: {request.exam_date}
Subjects: {subjects_str}
Daily Study Hours: {request.hours_per_day}
Current Level: {request.current_level}

Create an actionable 7-day calendar schedule with spaced repetition, breaks, and mock tests.
Return ONLY valid JSON matching this schema:
{{
    "exam_date": "{request.exam_date}",
    "daily_study_hours": {request.hours_per_day},
    "exam_tips": [
        "Use active recall over passive reading",
        "Take a 5-minute break every 25 minutes (Pomodoro technique)",
        "Review mistake logs before sleeping"
    ],
    "study_plan": [
        {{
            "day": "Day 1 (Monday)",
            "date_label": "Foundation Phase",
            "subjects": ["{request.subjects[0] if request.subjects else 'Subject 1'}"],
            "topics_to_cover": ["Core concepts & Formula derivations"],
            "practice_focus": "Solve 10 textbook examples",
            "revision_items": ["Flashcard deck: Definitions"],
            "break_recommendations": "10 min walk after 50 min block",
            "mock_test_scheduled": false
        }},
        {{
            "day": "Day 2 (Tuesday)",
            "date_label": "Application Phase",
            "subjects": ["{request.subjects[1] if len(request.subjects) > 1 else 'Subject 1'}"],
            "topics_to_cover": ["Advanced problem types & Algorithms"],
            "practice_focus": "Write 5 long-form exam answers",
            "revision_items": ["Review Day 1 mistakes"],
            "break_recommendations": "Hydration and stretching break",
            "mock_test_scheduled": false
        }},
        {{
            "day": "Day 3 (Wednesday)",
            "date_label": "Deep Dive Phase",
            "subjects": ["{request.subjects[0] if request.subjects else 'Subject 1'}"],
            "topics_to_cover": ["Tricky edge cases & past year questions"],
            "practice_focus": "Timed problem solving",
            "revision_items": ["Formula cheat sheet"],
            "break_recommendations": "Light physical exercise",
            "mock_test_scheduled": false
        }},
        {{
            "day": "Day 4 (Thursday)",
            "date_label": "Integration Phase",
            "subjects": ["{request.subjects[-1] if request.subjects else 'Subject 1'}"],
            "topics_to_cover": ["Cross-topic connections & case studies"],
            "practice_focus": "Diagnostic quiz",
            "revision_items": ["Spaced repetition flashcards"],
            "break_recommendations": "Eye relaxation and power nap",
            "mock_test_scheduled": false
        }},
        {{
            "day": "Day 5 (Friday)",
            "date_label": "Weak Area Sprint",
            "subjects": ["Focus on lowest scoring topics"],
            "topics_to_cover": ["Targeted remediations & Socratic tutoring"],
            "practice_focus": "Re-solve failed quiz questions",
            "revision_items": ["Summary notes"],
            "break_recommendations": "Healthy nutrition break",
            "mock_test_scheduled": false
        }},
        {{
            "day": "Day 6 (Saturday)",
            "date_label": "Full Simulation",
            "subjects": ["All Examination Subjects"],
            "topics_to_cover": ["Comprehensive syllabus"],
            "practice_focus": "Full length 3-hour mock exam in exam conditions",
            "revision_items": ["Audit mock test scoring"],
            "break_recommendations": "Extended break after mock exam",
            "mock_test_scheduled": true
        }},
        {{
            "day": "Day 7 (Sunday)",
            "date_label": "Final Polish & Mental Prep",
            "subjects": ["High-yield topics"],
            "topics_to_cover": ["Cheat sheet and diagrams only"],
            "practice_focus": "Mental walk-throughs",
            "revision_items": ["Quick revision 2-mark notes"],
            "break_recommendations": "Early sleep and calm evening walk",
            "mock_test_scheduled": false
        }}
    ]
}}
"""
        result = gemini_service.generate_json(prompt)
        plan_items: List[DailyScheduleItem] = []
        for item in result.get("study_plan", []):
            plan_items.append(DailyScheduleItem(**item))

        return StudyPlanResponse(
            exam_date=result.get("exam_date", request.exam_date),
            daily_study_hours=result.get("daily_study_hours", request.hours_per_day),
            study_plan=plan_items,
            exam_tips=result.get("exam_tips", [
                "Prioritize high-yield topics",
                "Review weak areas detected by EduGenie quizzes",
                "Ensure minimum 7 hours of restorative sleep"
            ])
        )

learning_path_service = LearningPathService()
