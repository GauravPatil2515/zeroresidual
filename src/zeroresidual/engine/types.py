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
    status: str  # SUCCESS, REFUNDED, PENDING
    payment_method: PaymentMethod = PaymentMethod.UPI
    customer_vpa: Optional[str] = None

class WebhookEvent(BaseModel):
    event_id: str
    order_id: str
    paytm_txn_id: str
    event_type: str  # PAYMENT_SUCCESS, REFUND_SUCCESS, CHARGEBACK_RAISED, AUTO_REVERSAL
    amount: Decimal
    status: str
    timestamp: str
    bank_ref_no: Optional[str] = None

class BankRecord(BaseModel):
    bank_ref_no: str
    utr_number: str
    amount: Decimal
    txn_type: str  # CR or DR
    narration: str
    timestamp: str

class WaterfallStep(BaseModel):
    category: DeductionCategory
    label: str
    amount: Decimal
    count: int
    direction: str  # "BASE", "SUBTRACT", "RESULT", "RESIDUAL"
    notes: str
    order_ids: List[str] = Field(default_factory=list)

class FactSheet(BaseModel):
    gross_pos: Decimal
    bank_received: Decimal
    refund_total: Decimal
    chargeback_total: Decimal
    cutoff_total: Decimal
    soundbox_fee_total: Decimal
    soundbox_gst_total: Decimal
    calculated_payout: Decimal
    residual: Decimal
    whitelist_numbers: List[str] = Field(default_factory=list)

class ReconciliationResult(BaseModel):
    scenario_name: str
    gross_pos_sales: Decimal
    bank_received_payout: Decimal
    total_deductions: Decimal
    expected_payout: Decimal
    residual: Decimal
    is_reconciled: bool
    status: str  # "RECONCILED" or "UNEXPLAINED_DISCREPANCY"
    exit_code: int
    waterfall: List[WaterfallStep]
    ledger_records: List[Dict[str, Any]]
    narration_audits: List[Dict[str, Any]]
    fact_sheet: FactSheet
    explanation_en: Optional[str] = None
    explanation_hinglish: Optional[str] = None
    dispute_payload: Optional[Dict[str, Any]] = None
