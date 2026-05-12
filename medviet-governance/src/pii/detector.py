import re
from dataclasses import dataclass


@dataclass
class RecognizerResult:
    entity_type: str
    start: int
    end: int
    score: float


class VietnamesePIIAnalyzer:
    """Small local analyzer for the lab's Vietnamese PII patterns."""

    PATTERNS = {
        "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "VN_CCCD": re.compile(r"\b\d{11,12}\b"),
        "VN_PHONE": re.compile(r"\b0?[35789]\d{8}\b"),
    }
    PERSON_PATTERN = re.compile(
        r"\b(?:Anh|Chị|Bà|Ông|Bác|Quý cô|Quý ông)?\s*"
        r"[A-ZÀ-Ỵ][A-Za-zÀ-ỹ]*(?:\s+[A-ZÀ-Ỵ][A-Za-zÀ-ỹ]*){1,4}\b"
    )

    def analyze(self, text: str, language: str = "vi", entities: list[str] | None = None) -> list[RecognizerResult]:
        requested = set(entities or ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"])
        results: list[RecognizerResult] = []

        for entity_type, pattern in self.PATTERNS.items():
            if entity_type not in requested:
                continue
            for match in pattern.finditer(text):
                results.append(RecognizerResult(entity_type, match.start(), match.end(), 0.9))

        if "PERSON" in requested:
            for match in self.PERSON_PATTERN.finditer(text):
                value = match.group(0).strip()
                if "@" not in value and not any(char.isdigit() for char in value):
                    results.append(RecognizerResult("PERSON", match.start(), match.end(), 0.75))

        return sorted(results, key=lambda result: (result.start, -result.end))


def build_vietnamese_analyzer() -> VietnamesePIIAnalyzer:
    return VietnamesePIIAnalyzer()


def detect_pii(text: str, analyzer: VietnamesePIIAnalyzer) -> list[RecognizerResult]:
    return analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
