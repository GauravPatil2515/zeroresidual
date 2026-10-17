import re
from typing import Optional, Tuple
from zeroresidual.adapters.base import BaseBankAdapter
from zeroresidual.engine.types import DeductionCategory

class HDFCBankAdapter(BaseBankAdapter):
    """
    Reference HDFC Bank Adapter.
    Handles settlement narrations such as:
    - UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-1011/HDFC
    - HDFC-DISPUTE-HOLD-DISP992
    """
    bank_code = "HDFC"

    def can_handle(self, narration: str) -> bool:
        upper = narration.upper()
        return "HDFC" in upper or "REFUND_ADJ" in upper

    def parse_narration(self, narration: str) -> Tuple[DeductionCategory, Optional[str]]:
        upper = narration.upper()
        order_match = re.search(r"ORD-\d+", upper)
        order_id = order_match.group(0) if order_match else None

        if "REFUND" in upper:
            return DeductionCategory.REFUND, order_id
        if "DISPUTE" in upper or "CHBK" in upper:
            return DeductionCategory.CHARGEBACK_HOLD, order_id
        if "SETTL" in upper or "NEFT" in upper:
            return DeductionCategory.SETTLED, None

        return DeductionCategory.UNEXPLAINED, order_id
