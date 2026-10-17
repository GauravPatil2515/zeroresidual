import re
from typing import Optional, Tuple
from zeroresidual.adapters.base import BaseBankAdapter
from zeroresidual.engine.types import DeductionCategory

class PaytmSoundboxAdapter(BaseBankAdapter):
    """
    Paytm Soundbox & Gateway Fee Adapter.
    Handles settlement narrations such as:
    - PAYTM-SNDBOX-RENTAL-OCT26-DEVICE-SN7719
    - GST@18%-ON-PAYTM-SOUNDBOX-CHARGES-HSN9983
    - CHBK-HOLD-DISP-992-ORD-1008-ICICI-ESCROW
    - NEFT-PAYTM-SETTL-OCT17-MID7721-UTR88912
    """
    bank_code = "PAYTM"

    def can_handle(self, narration: str) -> bool:
        upper = narration.upper()
        return any(k in upper for k in ["PAYTM", "SNDBOX", "SOUNDBOX", "GST", "CHBK", "NEFT"])

    def parse_narration(self, narration: str) -> Tuple[DeductionCategory, Optional[str]]:
        upper = narration.upper()
        order_match = re.search(r"ORD-\d+", upper)
        order_id = order_match.group(0) if order_match else None
        disp_match = re.search(r"DISP-\d+", upper)
        ref_id = order_id or (disp_match.group(0) if disp_match else None)

        if "GST" in upper:
            return DeductionCategory.SOUNDBOX_GST, None
        if "SNDBOX" in upper or "SOUNDBOX" in upper or "RENTAL" in upper:
            return DeductionCategory.SOUNDBOX_FEE, None
        if "CHBK" in upper or "DISP" in upper or "ESCROW" in upper:
            return DeductionCategory.CHARGEBACK_HOLD, ref_id
        if "REFUND" in upper:
            return DeductionCategory.REFUND, ref_id
        if "SETTL" in upper or "NEFT" in upper:
            return DeductionCategory.SETTLED, None

        return DeductionCategory.UNEXPLAINED, ref_id
