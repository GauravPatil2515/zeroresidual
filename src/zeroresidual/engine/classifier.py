import re
from typing import Tuple, Optional, Dict, Any
from zeroresidual.engine.types import DeductionCategory
from zeroresidual.adapters import get_registered_adapters
from zeroresidual.llm.gemma import GemmaClient

GEMMA_CLASSIFICATION_PROMPT = """You are a financial reconciliation parser specialized in Indian UPI and banking settlement narrations.
Analyze the following bank statement narration string and classify it into one of these strict categories:
- REFUND
- CHARGEBACK_HOLD
- SOUNDBOX_FEE
- SOUNDBOX_GST
- SETTLED
- UNEXPLAINED

Bank Narration: "{narration}"

You MUST respond strictly in valid JSON matching this schema:
{{
    "category": "<ONE_OF_THE_ABOVE_CATEGORIES>",
    "reference_id": "<Extracted order ID like ORD-1011 or dispute ID like DISP-992 or null>",
    "confidence": 0.95,
    "reasoning": "<Short 5-word explanation>"
}}
Do NOT output any markdown tags or text outside the JSON object.
"""

class NarrationClassifier:
    def __init__(self, gemma_client: Optional[GemmaClient] = None):
        self.adapters = get_registered_adapters()
        self.gemma = gemma_client or GemmaClient()

    def classify(self, narration: str, use_llm: bool = True) -> Tuple[DeductionCategory, Optional[str], str]:
        """
        Classifies bank narration string into:
        (category, reference_id, method_used)
        """
        # 1. First attempt with registered Bank Adapters (FOSS modularity)
        for adapter in self.adapters:
            if adapter.can_handle(narration):
                cat, ref = adapter.parse_narration(narration)
                if cat != DeductionCategory.UNEXPLAINED:
                    return cat, ref, f"ADAPTER:{adapter.bank_code}"

        # 2. If use_llm is True and Gemma is available, use semantic classification
        if use_llm and self.gemma.is_available():
            prompt = GEMMA_CLASSIFICATION_PROMPT.format(narration=narration)
            res = self.gemma.generate_json(prompt)
            if res and "category" in res:
                cat_str = res["category"].upper()
                ref = res.get("reference_id")
                try:
                    cat = DeductionCategory(cat_str)
                    return cat, ref, "LLM:GEMMA_2B"
                except ValueError:
                    pass

        # 3. Deterministic Regex Fallback (100% offline, zero-LLM guarantee)
        upper = narration.upper()
        order_match = re.search(r"ORD-\d+", upper)
        order_id = order_match.group(0) if order_match else None
        disp_match = re.search(r"DISP-\d+", upper)
        ref_id = order_id or (disp_match.group(0) if disp_match else None)

        if "GST" in upper:
            return DeductionCategory.SOUNDBOX_GST, None, "FALLBACK:REGEX"
        if "SNDBOX" in upper or "SOUNDBOX" in upper or "RENTAL" in upper:
            return DeductionCategory.SOUNDBOX_FEE, None, "FALLBACK:REGEX"
        if "CHBK" in upper or "DISPUTE" in upper or "ESCROW" in upper:
            return DeductionCategory.CHARGEBACK_HOLD, ref_id, "FALLBACK:REGEX"
        if "REFUND" in upper or "REV-UPI" in upper:
            return DeductionCategory.REFUND, ref_id, "FALLBACK:REGEX"
        if "SETTL" in upper or "NEFT" in upper:
            return DeductionCategory.SETTLED, None, "FALLBACK:REGEX"

        return DeductionCategory.UNEXPLAINED, ref_id, "FALLBACK:UNEXPLAINED"
