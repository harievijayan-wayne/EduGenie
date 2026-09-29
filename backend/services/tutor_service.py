import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services.gemini_service import gemini_service
from backend.schemas import TutorChatRequest, TutorChatResponse
from backend.models import TutorConversation, User
from backend.utils.text_utils import format_structured_response

class TutorService:
    def chat_with_tutor(
        self,
        request: TutorChatRequest,
        db: Session,
        user: Optional[User] = None
    ) -> TutorChatResponse:
        """
        Interactive Socratic AI Tutor.
        Guides the student step-by-step through guided inquiry, hints,
        and targeted practice instead of simply dumping answers.
        """
        user_id = user.id if user else None
        
        # Retrieve or create conversation record
        conv = None
        if request.conversation_id:
            conv = db.query(TutorConversation).filter(TutorConversation.id == request.conversation_id).first()
        
        if not conv:
            conv = TutorConversation(
                user_id=user_id,
                topic=request.topic or "Academic Guidance",
                history_json="[]"
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        history = json.loads(conv.history_json or "[]")

        # Tailor instruction based on user action buttons
        action_directive = ""
        if request.action == "explain_simpler":
            action_directive = "SPECIAL DIRECTIVE: The student asked for a much simpler explanation. Break it down using intuitive real-life imagery."
        elif request.action == "give_example":
            action_directive = "SPECIAL DIRECTIVE: The student wants another vivid, concrete example. Provide a fresh step-by-step example."
        elif request.action == "quiz_me":
            action_directive = "SPECIAL DIRECTIVE: Provide a quick conceptual check question to test the student's grasp on what was just discussed."
        elif request.action == "dont_understand":
            action_directive = "SPECIAL DIRECTIVE: The student is stuck and said 'I don't understand'. Validate their struggle with encouragement, isolate the tricky part, and guide them with a gentle hint."

        system_instruction = (
            "You are EduGenie's Personal AI Tutor — an exceptional Socratic educator.\n"
            "Format EVERY response with high visual structure:\n"
            "- Bold Section Headings (e.g. `### **1. Introduction & Overview**`)\n"
            "- Line-by-line detailed explanation using bullet points (`- **Concept:** explanation`)\n"
            "- Concrete step-by-step example section (`### **4. Practical Step-by-Step Example**`)\n"
            "- End with a reflective Socratic challenge (`### **5. Think About This**`)\n\n"
            "CRITICAL FORMAT RULES:\n"
            "1. MUST use markdown headers: `### **Heading Name**` with empty lines (\\n\\n) before and after.\n"
            "2. Explanations MUST be written line-by-line with bullet points: `- **Key Concept:** Line-by-line breakdown`.\n"
            "3. Put every single bullet point on its own new line. Never lump text into one paragraph.\n"
            "4. Provide a clear, worked example at the end with step-by-step points."
        )

        history_context = ""
        for turn in history[-6:]:  # recent 6 turns
            sender = "Student" if turn.get("role") == "user" else "EduGenie Tutor"
            history_context += f"{sender}: {turn.get('content', '')}\n"

        prompt = f"""
Current Topic: {request.topic}
Learner Level: {request.level}
{action_directive}

Conversation Context:
{history_context}
Student: {request.message}

Deliver your response in this EXACT structured layout:

### **1. Introduction & Overview**
- **Welcome & Context:** 1-2 sentence friendly introduction establishing what this topic is.
- **Why It Matters:** Why this concept is critical in the real world and where it is applied.

### **2. Line-by-Line Detailed Explanation**
- **Core Definition:** Plain-English, first-principles definition.
- **How It Works:** Step-by-step line-by-line breakdown of the internal mechanism.
- **Key Components:** Essential terminology and elements.
- **Important Invariants:** What rules or properties always hold true.

### **3. Key Insights & Takeaways**
- **Core Intuition:** The "aha moment" mental model.
- **Common Mistake:** The most common student error and how to avoid it.

### **4. Concrete Step-by-Step Example**
- **Real-World Analogy:** An intuitive everyday analogy (e.g. chef, library, traffic system).
- **Technical Walkthrough:** Concrete step-by-step example with inputs, actions, and output.

### **5. Think About This (Socratic Question)**
- **Guided Challenge:** A thought-provoking question to test the student's understanding.

Return ONLY valid JSON matching this schema:
{{
    "reply": "Full markdown-formatted response using the exact layout above with ### **Headings**, line-by-line bullet points (- **Bold Key:** explanation), and worked examples. Must use double newlines between sections.",
    "follow_up_questions": [
        "A deep thought-provoking question connecting this to what they just learned",
        "A question that asks them to apply this in a new scenario"
    ],
    "hints": [
        "A concrete hint that scaffolds without giving away the answer",
        "A second hint pointing to the key invariant or pattern"
    ],
    "socratic_tip": "An actionable study mindset tip specific to this topic"
}}
"""
        result = gemini_service.generate_json(prompt, system_instruction=system_instruction)

        raw_reply = (
            result.get("reply")
            or result.get("answer")
            or result.get("explanation")
            or result.get("simple_explanation")
            or result.get("content")
            or result.get("response")
            or result.get("text")
            or "That's a thoughtful question! Let's explore it together."
        )
        reply_text = format_structured_response(raw_reply)

        def safe_str_list(raw_items, default):
            if not isinstance(raw_items, list):
                return default
            res = []
            for it in raw_items:
                if isinstance(it, list):
                    res.extend(str(x) for x in it if x)
                elif it:
                    res.append(str(it))
            return res if res else default

        follow_ups = safe_str_list(result.get("follow_up_questions"), ["What would happen in the opposite scenario?"])
        hints = safe_str_list(result.get("hints"), ["Recall the core invariant."])
        socratic_tip = str(result.get("socratic_tip", "Active questioning builds deeper neural pathways."))

        # Update history
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": reply_text})
        conv.history_json = json.dumps(history[-20:])  # retain last 20 messages
        db.commit()

        return TutorChatResponse(
            reply=reply_text,
            conversation_id=conv.id,
            follow_up_questions=follow_ups,
            hints=hints,
            socratic_tip=socratic_tip
        )

tutor_service = TutorService()
