import re

PROHIBITED_TERMS = [
    r"\b(do i have)\b.*\b(cholera|typhoid|malaria|dengue|disease|sickness)\b",
    r"\b(diagnose me)\b",
    r"\b(what medication)\b",
    r"\b(prescribe)\b",
    r"\b(am i sick)\b",
    r"\b(treatment for)\b",
    r"\b(cure for)\b",
]

class SafetyViolation(Exception):
    def __init__(self, message="Query blocked by safety layer."):
        self.message = message
        super().__init__(self.message)

def check_query_safety(query: str):
    """
    Scans the user query for diagnostic or personal medical terminology.
    Raises SafetyViolation if the query violates the public-health non-diagnostic boundaries.
    """
    lower_query = query.lower()
    for pattern in PROHIBITED_TERMS:
        if re.search(pattern, lower_query):
            raise SafetyViolation(
                "I cannot diagnose an individual or provide medical advice. "
                "JalRakshak AI provides regional public-health risk intelligence. "
                "Please consult a healthcare professional for personal medical concerns."
            )
