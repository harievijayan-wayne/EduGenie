import re
import logging
import base64
from typing import Any, Dict, Optional
from backend.utils.json_utils import safe_json_parse

logger = logging.getLogger("edugenie.ollama")

# Options applied to every Ollama chat call.
# think=False disables qwen3's extended reasoning ("thinking") mode,
# which otherwise causes 1-3 minute delays before the first token.
_CHAT_OPTIONS = {"think": False}


def _strip_thinking(text: str) -> str:
    """Remove any <think>...</think> blocks that leak through despite think=False."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


class OllamaService:
    """
    EduGenie AI Service backed by a local Ollama instance.
    Communicates with qwen3:8b (or any configured Ollama model) via the
    official `ollama` Python SDK.  Exposes the same public interface as
    GeminiService so all upstream callers are model-agnostic.

    Thinking mode is explicitly disabled so responses are fast (~2–5 s).
    """

    def __init__(self, model: str = "qwen3:8b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self._client = None
        self._available = False
        self._init_client()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_client(self):
        """Try to connect to Ollama and verify the configured model exists."""
        try:
            import ollama  # noqa: PLC0415

            client = ollama.Client(host=self.host)
            # Quick connectivity check — list local models
            models_response = client.list()
            available_models = [m.model for m in (models_response.models or [])]
            available_bases = [
                m.split(":")[0] if ":" in m else m for m in available_models
            ]
            configured_base = self.model.split(":")[0]

            if self.model in available_models or configured_base in available_bases:
                self._client = client
                self._available = True
                logger.info(
                    f"Ollama service ready — model: {self.model} at {self.host} (thinking=OFF)"
                )
            else:
                logger.warning(
                    f"Ollama is running but model '{self.model}' is not pulled yet. "
                    f"Run:  ollama pull {self.model}"
                )
                self._client = client
                self._available = False
        except Exception as exc:
            logger.warning(
                f"Ollama not reachable at {self.host}: {exc}. "
                "EduGenie will fall back to Demo Mode."
            )
            self._client = None
            self._available = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return True only when Ollama is reachable AND the model is available."""
        return self._available

    def generate_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Generate a plain-text response from the Ollama model (thinking disabled)."""
        if not self._available or self._client is None:
            return self._fallback_text(prompt)

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat(
                model=self.model,
                messages=messages,
                options=_CHAT_OPTIONS,   # ← disables thinking mode
            )
            text = response.message.content or ""
            return _strip_thinking(text)
        except Exception as exc:
            logger.error(f"Ollama generate_text error: {exc}")
            return self._fallback_text(prompt)

    def generate_json(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured JSON response from the Ollama model (thinking disabled)."""
        structured_prompt = (
            f"{prompt}\n\n"
            "CRITICAL: Output ONLY a valid raw JSON object. "
            "Do not include markdown formatting, code fences, or any explanation text."
        )
        if not self._available or self._client is None:
            return self._fallback_json(prompt)

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": structured_prompt})

            response = self._client.chat(
                model=self.model,
                messages=messages,
                format="json",           # Ollama structured output mode
                options=_CHAT_OPTIONS,   # ← disables thinking mode
            )
            raw = _strip_thinking(response.message.content or "")
            parsed = safe_json_parse(raw)
            if parsed is not None:
                return parsed

            # Retry: ask the model to fix its own malformed output
            fix_messages = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "The JSON you produced is malformed. "
                        "Return ONLY a corrected, valid JSON object with no extra text."
                    ),
                },
            ]
            retry = self._client.chat(
                model=self.model,
                messages=fix_messages,
                format="json",
                options=_CHAT_OPTIONS,
            )
            parsed_retry = safe_json_parse(_strip_thinking(retry.message.content or ""))
            if parsed_retry is not None:
                return parsed_retry
        except Exception as exc:
            logger.error(f"Ollama generate_json error: {exc}")

        return self._fallback_json(prompt)

    def generate_multimodal(
        self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> str:
        """
        Send an image + text prompt to the Ollama model (thinking disabled).
        Note: qwen3:8b does not support vision natively; use llava for image tasks.
        """
        if not self._available or self._client is None:
            return self._fallback_multimodal()

        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = self._client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [b64_image],
                    }
                ],
                options=_CHAT_OPTIONS,   # ← disables thinking mode
            )
            return _strip_thinking(response.message.content or "")
        except Exception as exc:
            logger.error(
                f"Ollama generate_multimodal error: {exc}. "
                "Note: qwen3:8b may not support vision — consider using llava."
            )
            return self._fallback_multimodal()

    # ------------------------------------------------------------------
    # Fallbacks
    # ------------------------------------------------------------------

    def _fallback_text(self, prompt: str) -> str:
        p = prompt.lower()
        if "tamil" in p or "tanglish" in p:
            return (
                "EduGenie AI Explanation (Tanglish):\n"
                "Intha concept romba simple! Neenga visualize panni paatha easy-ah purinjikkalam.\n"
                "Mukkiyamaana 3 points:\n"
                "1. Core concept purinjikonga, formula-va mattum direct-ah memorize pannaadheenga.\n"
                "2. Real-world example: Phone battery or computer memory maari relate pannunga.\n"
                "3. Regular practice pannum podhu exam-la 100% full marks score panna mudiyum!"
            )
        elif "eli5" in p or "5 year old" in p:
            return (
                "Imagine you have a magical toy box. Every time you ask for a toy, "
                "the box instantly finds it and hands it to you without making a mess! "
                "That's exactly how this concept works—it takes complex steps and makes them smooth and effortless."
            )
        return (
            "### EduGenie Academic Breakdown\n\n"
            "**Core Concept Overview:**\n"
            "This topic is a cornerstone of modern academics and engineering problem solving. "
            "It operates on established first principles where state transitions and data flows interact predictably.\n\n"
            "**Key Pillars:**\n"
            "1. **Foundational Invariants:** Every operation maintains logical integrity.\n"
            "2. **Optimal Strategy:** Breaking down the problem into sub-problems yields higher efficiency.\n"
            "3. **Practical Application:** Widely adopted in production software, distributed systems, and scientific computing.\n\n"
            "**Summary:** Master the fundamentals first, verify edge cases, and apply hands-on practice problems."
        )

    def _fallback_json(self, prompt: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "content": "EduGenie AI (Ollama) processed the educational query.",
            "highlights": ["Accuracy", "Clarity", "Step-by-Step Pedagogical Guidance"],
        }

    def _fallback_multimodal(self) -> str:
        return (
            "[EduGenie AI Analysis]\n"
            "This document or visual learning asset contains educational diagrams and instructional problem steps. "
            "Key Observations:\n"
            "1. The visual presents structured components with input-to-output transformations.\n"
            "2. Fundamental theorem and problem definition are clearly highlighted.\n"
            "3. Step-by-step mathematical or algorithmic derivations should be followed from top-left to bottom-right."
        )


# ---------------------------------------------------------------------------
# Singleton — imported by other modules
# ---------------------------------------------------------------------------
from backend.config import settings  # noqa: E402

ollama_service = OllamaService(
    model=settings.OLLAMA_MODEL,
    host=settings.OLLAMA_HOST,
)
