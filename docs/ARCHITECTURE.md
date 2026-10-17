# 🏛️ ZeroResidual System Architecture

ZeroResidual is an open-source, air-gapped reconciliation and discrepancy detection engine designed specifically for the Indian payments ecosystem (UPI, NetBanking, Cards, Soundbox).

```
                      +-----------------------------+
                      |   1. POS Orders (CSV)       |
                      |   (Gross Captured Sales)    |
                      +--------------+--------------+
                                     |
                                     v
+-----------------------------+      |      +------------------------------+
| 2. Gateway Webhooks (JSON)  | ---> | <--- | 3. Bank Statement (CSV)      |
| (Refunds, Holds, Cutoffs)   |      |      | (HDFC, SBI, Paytm UTR)       |
+-----------------------------+      v      +------------------------------+
                       +---------------------------+
                       |    Pluggable Adapters     |
                       |    (Statement Normalizer) |
                       +-------------+-------------+
                                     |
                                     v
                       +---------------------------+
                       |   Dual-Mode Classifier    |
                       |  - Fast Regex (<5ms)      |
                       |  - Local Gemma 2 (2B)     |
                       +-------------+-------------+
                                     |
                                     v
                       +---------------------------+
                       |   Decimal Recon Engine    |
                       |   (Exact Paisa Math)      |
                       +-------------+-------------+
                                     |
                                     v
                       +---------------------------+
                       |   Number Guard Validator  |
                       |   (Fact Sheet Enforcer)   |
                       +-------------+-------------+
                                     |
                   +-----------------+-----------------+
                   |                                   |
                   v                                   v
        +---------------------+             +---------------------+
        | Residual == ₹0.00   |             | Residual != ₹0.00   |
        | Exit Code: 0        |             | Exit Code: 1        |
        | Status: RECONCILED  |             | Status: UNEXPLAINED |
        +---------------------+             +---------------------+
```

---

## 1. The Three Financial Ingestion Streams

### Stream 1: Merchant POS Transactions (`pos_orders.csv`)
* Origin: Merchant billing system, POS terminals, or e-commerce backends.
* Fields: `order_id`, `amount`, `status`, `timestamp_ist`, `payment_method`.
* Representation: The baseline expectation of gross revenue captured for the settlement batch.

### Stream 2: Payment Gateway S2S Webhooks (`webhooks.json`)
* Origin: Paytm, Razorpay, Cashfree, or PhonePe server-to-server callbacks.
* Fields: `event`, `order_id`, `amount`, `timestamp_ist`, `reason`, `dispute_id`.
* Events Handled:
  - `charge.refunded`: Full or partial refund initiated to the customer.
  - `charge.dispute_hold`: Buyer disputed the transaction; gateway locked funds in escrow pending proof of delivery.
  - `cutoff.delayed`: Transaction completed after 23:00 IST cutoff window; deferred to T+1 cycle.

### Stream 3: Bank Settlement Feed (`bank_settlement.csv`)
* Origin: Core Banking System (CBS) statements via NetBanking CSV exports (HDFC, SBI, Paytm Payments Bank).
* Fields: `date`, `narration`, `ref_utr`, `withdrawal_debit`, `deposit_credit`, `balance`.
* Non-Standard Narrations:
  - Payout UTR deposits: `CMS/PAYTM/UTR99104.../SETTL`
  - Soundbox IoT subscription fees: `POS SERVICE RENTAL 4G IOT`
  - GST clawbacks: `GST@18% ON DEVICE RENTAL`
  - Chargeback debits: `REV/UPI/CR/DISP-992`

---

## 2. Pluggable Bank Adapters

Every Indian commercial bank formats narration lines differently. ZeroResidual uses an extensible adapter pattern:

```python
class BankAdapter(ABC):
    @abstractmethod
    def parse_statement(self, filepath: str) -> List[NormalizedBankRow]:
        """Convert heterogeneous bank CSV rows into normalized Decimal transactions."""
        pass
```

Included adapters:
* **HDFC Adapter (`adapters/hdfc.py`):** Handles `CMS/` prefixes, cheque reference numbers, and integrated chargeback reversal formats.
* **SBI Adapter (`adapters/sbi.py`):** Parses State Bank of India corporate current account descriptions, clearing codes, and NEFT/RTGS UTR sequences.
* **Paytm Adapter (`adapters/paytm.py`):** Parses daily consolidated merchant settlement credits, Soundbox 4G hardware rentals, and statutory GST splits.

---

## 3. Strict Decimal Precision Model

Standard IEEE-754 floating-point math leads to catastrophic precision drift in financial applications:
```python
>>> 0.1 + 0.2
0.30000000000000004
```

ZeroResidual enforces `decimal.Decimal` throughout the codebase:
* All currency quantities are instantiated from exact strings.
* Calculations maintain exact 2-decimal precision (e.g. ₹423.73 Soundbox rental + ₹76.27 GST = ₹500.00).
* Any floating-point instantiation raises a type validation error in Pydantic models.

---

## 4. Anti-Hallucination Number Guard (`NumberGuard`)

Large Language Models frequently hallucinate numbers when explaining financial statements. ZeroResidual introduces a strict security boundary:

1. **Fact Sheet Extraction:** Before invoking the LLM, the engine extracts every valid financial figure from the deterministic calculations (Gross, Deductions, Net, Residual, Order IDs, UTRs).
2. **Regex Interception:** Any response from Google Gemma is parsed with `r'(\d+[\d,]*\.?\d*)'` to identify all emitted numbers.
3. **Set Containment Verification:** If any emitted number is not found in the pre-approved Fact Sheet, the LLM output is rejected immediately, and a deterministic audited template is served.

This guarantees that ZeroResidual **never exposes hallucinated financial advice to a merchant or auditor.**
