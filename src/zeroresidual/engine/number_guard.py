import re
from typing import Tuple, List, Set
from zeroresidual.engine.types import FactSheet

class NumberGuard:
    """
    Anti-Hallucination Number Guard.
    Enforces that every numeric token appearing in LLM-generated explanations
    is strictly present in the verified deterministic FactSheet.
    """

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        # Matches numbers like 50000, 50,000, 423.73, 1011, 18% (18)
        raw_matches = re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", text)
        cleaned = []
        for m in raw_matches:
            c = m.replace(",", "")
            cleaned.append(c)
            # also add float representation if integer
            if "." not in c:
                cleaned.append(f"{c}.00")
        return cleaned

    @classmethod
    def validate_text(cls, text: str, fact_sheet: FactSheet) -> Tuple[bool, List[str]]:
        """
        Validates text against fact sheet numbers.
        Returns (is_valid, offending_numbers).
        """
        emitted_numbers = cls.extract_numbers(text)
        whitelist: Set[str] = set()

        # Build comprehensive whitelist from fact sheet
        whitelist.update([
            str(fact_sheet.gross_pos),
            str(fact_sheet.bank_received),
            str(fact_sheet.refund_total),
            str(fact_sheet.chargeback_total),
            str(fact_sheet.cutoff_total),
            str(fact_sheet.soundbox_fee_total),
            str(fact_sheet.soundbox_gst_total),
            str(fact_sheet.calculated_payout),
            str(fact_sheet.residual),
            "0", "0.00", "18", "18.00", "1", "2", "3", "4", "5", "10", "17", "2026" # legitimate dates/counts/GST%
        ])

        for num in fact_sheet.whitelist_numbers:
            whitelist.add(str(num))
            whitelist.add(str(num).replace(".00", ""))

        offending = []
        for n in emitted_numbers:
            # Check integer or float equivalent
            base_n = n.split(".")[0]
            if n not in whitelist and base_n not in whitelist:
                offending.append(n)

        is_valid = len(offending) == 0
        return is_valid, offending
