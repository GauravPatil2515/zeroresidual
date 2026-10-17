from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

def to_decimal(val: Any) -> Decimal:
    """Safely convert any numeric value or string to Decimal rounded to 2 places (paise)."""
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class DeductionCategory(str, Enum):
    REFUND = "REFUND"
    CHARGEBACK_HOLD = "CHARGEBACK_HOLD"
    CUTOFF_DELAY = "CUTOFF_DELAY"
    SOUNDBOX_FEE = "SOUNDBOX_FEE"
    SOUNDBOX_GST = "SOUNDBOX_GST"
    CARD_MDR_FEE = "CARD_MDR_FEE"
    SETTLED = "SETTLED"
    UNEXPLAINED = "UNEXPLAINED"

class PaymentMethod(str, Enum):
    UPI = "UPI"
    DEBIT_CARD = "DEBIT_CARD"
    CREDIT_CARD = "CREDIT_CARD"
    NETBANKING = "NETBANKING"

class POSOrder(BaseModel):
    order_id: str
    amount: Decimal
    timestamp: str
    status: str
    payment_method: PaymentMethod = PaymentMethod.UPI
    customer_vpa: Optional[str] = None
