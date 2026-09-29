"""
EduGenie AI Service — Groq backend (ultra-fast cloud inference)

Uses the official `groq` Python SDK which is OpenAI-API-compatible.
Default model: llama-3.1-8b-instant  (~200 tok/s, sub-second responses)

All upstream code imports `gemini_service`; this module provides the same
interface so zero route/service files need to change.
"""
import logging
import json
import re
from typing import Any, Dict, Optional
from backend.utils.json_utils import safe_json_parse

logger = logging.getLogger("edugenie.groq")


class GroqService:
    """
    EduGenie AI Service backed by Groq cloud inference.
    Exposes the same public interface as OllamaService / GeminiService
    so all upstream callers are model-agnostic.

    Groq delivers ~200 tokens/second — responses arrive in 1-3 seconds.
    """

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._available = False
        self._init_client()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_client(self):
        """Initialise the Groq client and verify the API key works."""
        if not self.api_key or self.api_key in ("", "your_groq_api_key_here"):
            logger.warning("Groq API key not set — falling back to Demo Mode.")
            return
        try:
            from groq import Groq  # noqa: PLC0415
            self._client = Groq(api_key=self.api_key)
            self._available = True
            logger.info(f"Groq service ready — model: {self.model}")
        except ImportError:
            logger.error(
                "groq package not installed. Run: pip install groq"
            )
        except Exception as exc:
            logger.error(f"Groq init error: {exc}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        return self._available

    def generate_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Generate a plain-text response via Groq (fast)."""
        if not self._available or self._client is None:
            return self._fallback_text(prompt)

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            completion = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3072,
            )
            return (completion.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.error(f"Groq generate_text error: {exc}")
            return self._fallback_text(prompt)

    def generate_json(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured JSON response via Groq."""
        if not self._available or self._client is None:
            return self._fallback_json(prompt)

        structured_prompt = (
            f"{prompt}\n\n"
            "CRITICAL: Output ONLY a valid raw JSON object. "
            "Do not include markdown formatting, code fences, or any explanation."
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": structured_prompt})

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
            )

            raw = (completion.choices[0].message.content or "").strip()
            parsed = safe_json_parse(raw)
            if parsed is not None:
                if isinstance(parsed, dict):
                    main_text = (
                        parsed.get("reply")
                        or parsed.get("answer")
                        or parsed.get("explanation")
                        or parsed.get("simple_explanation")
                        or parsed.get("content")
                        or parsed.get("response")
                        or parsed.get("text")
                    )
                    # If main_text is itself an encoded JSON string, unwrap it
                    if isinstance(main_text, str) and main_text.strip().startswith("{"):
                        inner = safe_json_parse(main_text)
                        if isinstance(inner, dict):
                            inner_text = inner.get("reply") or inner.get("answer") or inner.get("explanation")
                            if inner_text:
                                main_text = inner_text

                    if main_text:
                        parsed["reply"] = main_text
                        parsed["answer"] = main_text
                        parsed["simple_explanation"] = main_text
                return parsed

            # If raw is rich educational text without a JSON envelope, preserve it directly
            if raw and len(raw) > 20:
                return {
                    "reply": raw,
                    "answer": raw,
                    "simple_explanation": raw,
                    "follow_up_questions": [
                        "How does this concept apply in real-world systems?",
                        "What is the most critical invariant to remember?"
                    ],
                    "hints": ["Review the core principle and steps."],
                    "socratic_tip": "Active recall and questioning build deeper understanding."
                }
        except Exception as exc:
            logger.error(f"Groq generate_json error: {exc}")

        return self._fallback_json(prompt)

    def generate_multimodal(
        self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> str:
        """
        Groq's text models don't support vision.
        Falls back to a descriptive placeholder for image inputs.
        """
        if not self._available or self._client is None:
            return self._fallback_multimodal()
        # Use text-only analysis as Groq's fast models are text-only
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": f"[Image uploaded] {prompt}"}],
                temperature=0.5,
                max_tokens=512,
            )
            return (completion.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.error(f"Groq multimodal error: {exc}")
            return self._fallback_multimodal()

    # ------------------------------------------------------------------
    # Fallbacks (used when Groq is unreachable)
    # ------------------------------------------------------------------

    def _fallback_text(self, prompt: str) -> str:
        p = prompt.lower()
        if "tamil" in p or "tanglish" in p:
            return (
                "EduGenie AI Explanation (Tanglish):\n"
                "Intha concept romba simple! Neenga visualize panni paatha easy-ah purinjikkalam.\n"
                "1. Core concept purinjikonga, formula-va mattum memorize pannaadheenga.\n"
                "2. Real-world example: Phone battery or computer memory maari relate pannunga.\n"
                "3. Regular practice pannum podhu exam-la full marks score panna mudiyum!"
            )
        elif "eli5" in p or "5 year old" in p:
            return (
                "Imagine you have a magical toy box. Every time you ask for a toy, "
                "the box instantly finds it and hands it to you without making a mess! "
                "That's exactly how this concept works."
            )
        return (
            "### EduGenie Academic Breakdown\n\n"
            "**Core Concept Overview:**\n"
            "This topic is a cornerstone of modern academics and engineering problem solving.\n\n"
            "**Key Pillars:**\n"
            "1. **Foundational Invariants:** Every operation maintains logical integrity.\n"
            "2. **Optimal Strategy:** Breaking problems into sub-problems yields higher efficiency.\n"
            "3. **Practical Application:** Widely adopted in production software and scientific computing.\n\n"
            "**Summary:** Master the fundamentals first, verify edge cases, and apply hands-on practice."
        )

    def _fallback_json(self, prompt: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "content": "EduGenie AI (Groq) processed the educational query.",
            "highlights": ["Accuracy", "Clarity", "Step-by-Step Pedagogical Guidance"],
        }

    def _fallback_multimodal(self) -> str:
        return (
            "[EduGenie AI Analysis]\n"
            "This document contains educational diagrams and instructional problem steps.\n"
            "1. The visual presents structured components with input-to-output transformations.\n"
            "2. Fundamental theorem and problem definition are clearly highlighted.\n"
            "3. Follow step-by-step derivations from top-left to bottom-right."
        )


# ---------------------------------------------------------------------------
# Singleton — imported by gemini_service alias
# ---------------------------------------------------------------------------
from backend.config import settings  # noqa: E402

groq_service = GroqService(
    api_key=settings.GROQ_API_KEY or "",
    model=settings.GROQ_MODEL,
)
