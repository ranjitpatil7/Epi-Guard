import spacy
from typing import Dict, Any, List

# Load small english model (requires `python -m spacy download en_core_web_sm` to be run)
# We will gracefully fall back to pure keywords if spacy model is not downloaded yet
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

class ReportNLPService:
    """
    Advanced Community Report NLP Pipeline (Phase 4).
    Extracts structured signals from natural language reports without requiring an LLM.
    """
    
    KEYWORD_MAPPING = {
        "flooding": ["flood", "flooding", "submerged", "overflow", "inundated", "heavy rain"],
        "water_quality": ["muddy", "brown", "smell", "dirty", "contaminated", "turbid", "yellow"],
        "disease": ["stomach", "illness", "diarrhea", "cholera", "sick", "vomiting", "fever"],
        "sanitation": ["sewage", "drain", "garbage", "waste", "toilet"]
    }
    
    URGENCY_KEYWORDS = ["urgent", "help", "emergency", "immediate", "dying", "severe"]

    @staticmethod
    def process_report(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        signals = []
        severity = "LOW"
        urgency = "NORMAL"
        confidence = 0.5 # Base confidence for simple keyword matching
        
        # 1. SpaCy Entity Extraction (if available)
        entities = []
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append({"text": ent.text, "label": ent.label_})
            confidence += 0.2
            
        # 2. Keyword Classification
        for category, words in ReportNLPService.KEYWORD_MAPPING.items():
            if any(word in text_lower for word in words):
                signals.append(category)
                
        if any(word in text_lower for word in ReportNLPService.URGENCY_KEYWORDS):
            urgency = "HIGH"
            
        # 3. Determine Severity
        if "disease" in signals and "water_quality" in signals:
            severity = "HIGH"
        elif "disease" in signals or ("flooding" in signals and "water_quality" in signals):
            severity = "MODERATE"
        elif len(signals) > 0:
            severity = "GUARDED"
            
        if urgency == "HIGH":
            severity = "HIGH" if severity in ["MODERATE", "GUARDED", "LOW"] else "CRITICAL"
            
        # 4. Final output
        return {
            "severity": severity,
            "signals": signals,
            "urgency": urgency,
            "entities": entities,
            "confidence": min(1.0, round(confidence + (len(signals) * 0.1), 2))
        }
