import re
import unicodedata

_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)
_MULTI_SPACE = re.compile(r"\s+")
_REPEATED_PUNCTUATION = re.compile(r"([،,;؛])\1+")


def normalize_arabic_address(text: str) -> str:
    """
    Conservative normalization for Palestinian descriptive addresses.

    We intentionally do NOT collapse characters such as ة/ه or ى/ي here,
    because the raw linguistic form may be useful for later NLP and alias
    resolution. Matching-specific normalization can be added separately.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ـ", "")
    text = _ARABIC_DIACRITICS.sub("", text)

    # Normalize whitespace and common separators while preserving Arabic text.
    text = text.replace("\n", " ").replace("\t", " ")
    text = _REPEATED_PUNCTUATION.sub(r"\1", text)
    text = _MULTI_SPACE.sub(" ", text)

    return text.strip()
