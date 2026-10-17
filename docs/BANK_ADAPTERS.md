# 🏦 Bank Statement Adapters Specification

ZeroResidual supports pluggable bank statement adapters to parse heterogeneous transaction exports from Indian commercial banks into normalized `NormalizedBankRow` structures.

---

## 1. Adapter Contract

All bank adapters inherit from `BaseBankAdapter` in `src/zeroresidual/adapters/base.py`:

```python
from abc import ABC, abstractmethod
from typing import List
from zeroresidual.engine.types import NormalizedBankRow

class BaseBankAdapter(ABC):
    """Abstract Base Class for Indian Bank Statement Parsers."""
    
    @property
    @abstractmethod
    def bank_code(self) -> str:
        """Unique identifier (e.g. 'HDFC', 'SBI', 'PAYTM', 'ICICI')."""
        pass

    @abstractmethod
    def parse_statement(self, filepath: str) -> List[NormalizedBankRow]:
        """Parse raw bank CSV into normalized Decimal rows."""
        pass
```

---

## 2. Standard Normalized Model

Every parsed line produces a `NormalizedBankRow`:

| Field | Type | Description |
| :--- | :--- | :--- |
| `date` | `str` | ISO formatted date (`YYYY-MM-DD`) |
| `narration` | `str` | Raw original bank narration string |
| `ref_utr` | `Optional[str]` | Extracted 12-to-22 character UTR / RRN |
| `withdrawal` | `Decimal` | Debit amount (default `Decimal("0.00")`) |
| `deposit` | `Decimal` | Credit amount (default `Decimal("0.00")`) |
| `balance` | `Optional[Decimal]` | Running balance after transaction |

---

## 3. Implemented Adapters

### HDFC Bank Adapter (`adapters/hdfc.py`)
* **Typical Narration:** `CMS/PAYTM/UTR99104001882/SETTL` or `REV/UPI/CR/DISP-992`
* **Regex Extraction:** Captures UTRs following `CMS/` or `INF/NEFT/`. Identifies reversals and disputes via `REV/UPI` or `CHARGEBACK`.

### SBI Corporate Adapter (`adapters/sbi.py`)
* **Typical Narration:** `TRANSFER-UPI/CR/429188219012/PAYTM` or `REV-UPI/DISPUTE-992`
* **Regex Extraction:** Extracts 12-digit RRN numbers and flags `REV-UPI` clawbacks.

### Paytm Payments Bank Adapter (`adapters/paytm.py`)
* **Typical Narration:**
  - Consolidated Settlement: `PAYTM SETTLEMENT UTR: PAYTM99104001882`
  - IoT Soundbox Rental: `POS SERVICE RENTAL 4G IOT`
  - GST Deduction: `GST@18% ON DEVICE RENTAL`
* **Features:** Automatically detects hardware subscription line items and maps statutory GST breakdowns.

---

## 4. How to Add a New Bank Adapter (e.g., ICICI)

To add support for ICICI Bank:
1. Create `src/zeroresidual/adapters/icici.py`.
2. Implement `BaseBankAdapter`.
3. Register the adapter in `src/zeroresidual/adapters/__init__.py`.
4. Add a test in `tests/test_adapters.py`.
