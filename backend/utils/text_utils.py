import re
from typing import List

def clean_text(text: str) -> str:
    """Removes redundant whitespaces, carriage returns, and control characters."""
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 120) -> List[str]:
    """
    Splits text into overlapping chunks respecting sentence or paragraph boundaries.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    # Split by paragraphs or double newlines first
    paragraphs = [p.strip() for p in cleaned.split('\n\n') if p.strip()]
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for paragraph in paragraphs:
        # If single paragraph is larger than chunk_size, split by sentences
        if len(paragraph) > chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence_len = len(sentence)
                if current_length + sentence_len > chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Overlap: keep the last sentence
                    current_chunk = [current_chunk[-1]] if len(current_chunk) > 0 else []
                    current_length = len(current_chunk[0]) if current_chunk else 0
                current_chunk.append(sentence)
                current_length += sentence_len
        else:
            if current_length + len(paragraph) > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(paragraph)
            current_length += len(paragraph)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def estimate_reading_time_minutes(text: str) -> int:
    """Calculates approximate reading time based on standard 200 wpm."""
    words = len(text.split())
    return max(1, round(words / 200))


def format_structured_response(text: str) -> str:
    """
    Ensures AI responses are cleanly formatted with bold headings,
    line-by-line bullet points, and proper double newlines for markdown rendering.
    """
    if not text:
        return ""
    text = str(text).replace('\\n', '\n').replace('\r\n', '\n').replace('\r', '\n')

    # Remove stray standalone # characters on their own line
    text = re.sub(r'(?m)^\s*#\s*$', '', text)
    text = re.sub(r'^\s*#\s*\n+', '', text)

    # Ensure double newlines before markdown headings (###, ##)
    text = re.sub(r'([^\n])\s*(#{1,4}\s+[^\n]+)', r'\1\n\n\2\n', text)

    # Clean up empty bullets like "-\n\n**" or "-\n**" so bullet and bold header stay together
    text = re.sub(r'-\s*\n+\s*(\*\*)', r'- \1', text)

    # Ensure double newlines before standalone bold section headers (when not part of a bullet)
    text = re.sub(r'([.!?])\s*(\*\*[A-Z][a-zA-Z0-9\s\/\-_]{1,40}:\*\*)', r'\1\n\n\2 ', text)

    # Ensure bullet or numbered items clumped inline get their own lines
    text = re.sub(r'([^\n])\s*(\d+\.\s+\*\*)', r'\1\n- \2', text)
    text = re.sub(r'([^\n])\s*(-\s+\*\*)', r'\1\n\2', text)

    # Reconnect bullet bold headers with following text if broken across lines
    text = re.sub(r'(- \*\*[^*]+:\*\*)\n\s*([A-Za-z0-9])', r'\1 \2', text)

    # Clean up redundant blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


