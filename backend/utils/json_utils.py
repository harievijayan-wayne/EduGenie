import json
import re
from typing import Any, Optional

def clean_json_block(raw_text: str) -> str:
    """
    Cleans markdown formatting, code fences (e.g. ```json ... ```), 
    and leading/trailing whitespace from AI generated JSON strings.
    """
    if not raw_text:
        return ""
    
    cleaned = raw_text.strip()
    
    # Strip markdown ```json or ``` code fences
    fence_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.search(fence_pattern, cleaned, re.MULTILINE)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Also handle cases where fences are not strictly at start/end
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    return cleaned

def safe_json_parse(raw_text: str, default: Any = None) -> Any:
    """
    Attempts to safely parse JSON text. If direct parsing fails,
    tries extracting JSON substring between first { / [ and last } / ],
    permits non-strict parsing for unescaped newlines/control characters,
    and falls back to regex key extraction for AI outputs.
    """
    if not raw_text:
        return default
        
    cleaned = clean_json_block(raw_text)
    
    # 1. Direct parse (standard + non-strict)
    for strict in (True, False):
        try:
            return json.loads(cleaned, strict=strict)
        except (json.JSONDecodeError, TypeError):
            pass
        
    # 2. Locate outer JSON object {...}
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate_obj = cleaned[first_brace:last_brace + 1]
        for strict in (True, False):
            try:
                return json.loads(candidate_obj, strict=strict)
            except (json.JSONDecodeError, TypeError):
                pass

    # 3. Locate outer JSON array [...]
    first_bracket = cleaned.find('[')
    last_bracket = cleaned.rfind(']')
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate_arr = cleaned[first_bracket:last_bracket + 1]
        for strict in (True, False):
            try:
                return json.loads(candidate_arr, strict=strict)
            except (json.JSONDecodeError, TypeError):
                pass

    # 4. Regex key extraction fallback for AI output
    extracted = {}
    reply_match = re.search(r'"(?:reply|answer|simple_explanation)"\s*:\s*"([\s\S]*?)(?="\s*,\s*"[a-zA-Z_]+"\s*:|"\s*\}\s*$)', cleaned)
    if reply_match:
        val = reply_match.group(1).replace('\\"', '"').replace('\\n', '\n')
        extracted["reply"] = val
        extracted["answer"] = val
        extracted["simple_explanation"] = val
        return extracted

    return default
