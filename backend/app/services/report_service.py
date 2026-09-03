from typing import Dict, Any

class ReportNLPService:
    """
    Analyzes community reports for public health risk signals.
    Phase 2 Stub: Simple keyword matching. Phase 3 will use LLM/Transformer.
    """
    
    HIGH_RISK_KEYWORDS = ["diarrhea", "cholera", "vomiting", "death", "outbreak", "dirty water", "fever"]
    MEDIUM_RISK_KEYWORDS = ["sick", "stomach", "pain", "muddy", "smell"]
    
    @staticmethod
    def analyze_report(text: str) -> Dict[str, Any]:
        """
        Calculates an NLP severity score (0.0 to 1.0).
        """
        text_lower = text.lower()
        score = 0.0
        
        for kw in ReportNLPService.HIGH_RISK_KEYWORDS:
            if kw in text_lower:
                score += 0.4
                
        for kw in ReportNLPService.MEDIUM_RISK_KEYWORDS:
            if kw in text_lower:
                score += 0.2
                
        final_severity = min(1.0, score)
        
        return {
            "nlp_severity": final_severity,
            "status": "FLAGGED" if final_severity > 0.5 else "PENDING",
            "keywords_found": [kw for kw in ReportNLPService.HIGH_RISK_KEYWORDS + ReportNLPService.MEDIUM_RISK_KEYWORDS if kw in text_lower]
        }
