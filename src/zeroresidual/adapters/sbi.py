import re
from typing import Optional, Tuple
from zeroresidual.adapters.base import BaseBankAdapter
from zeroresidual.engine.types import DeductionCategory

class SBIBankAdapter(BaseBankAdapter):
    """
    Reference State Bank of India (SBI) Adapter.
    Handles settlement narrations such as:
    - REV-UPI-REFUND-PAYTM-ORD-1025-SBI
    - SBI-PAYTM-DISP-HOLD
    """
    bank_code = "SBI"

    def can_handle(self, narration: str) -> bool:
        upper = narration.upper()
        return "SBI" in upper or "REV-UPI" in upper

    def parse_narration(self, narration: str) -> Tuple[DeductionCategory, Optional[str]]:
        upper = narration.upper()
        order_match = re.search(r"ORD-\d+", upper)
        order_id = order_match.group(0) if order_match else None

        if "REFUND" in upper or "REV" in upper:
            return DeductionCategory.REFUND, order_id
        if "DISP" in upper or "HOLD" in upper:
            return DeductionCategory.CHARGEBACK_HOLD, order_id
        if "SETTL" in upper or "NEFT" in upper:
            return DeductionCategory.SETTLED, None

        return DeductionCategory.UNEXPLAINED, order_id
