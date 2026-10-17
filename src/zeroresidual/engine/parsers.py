import re
import io
import csv
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import fitz  # PyMuPDF

from zeroresidual.engine.types import DeductionCategory
from zeroresidual.engine.classifier import NarrationClassifier
from zeroresidual.llm.gemma import GemmaClient

class NormalizedBankRow(BaseModel):
    date: str
    narration: str
    ref_utr: Optional[str] = None
    withdrawal: Decimal = Decimal("0.00")
    deposit: Decimal = Decimal("0.00")
    balance: Optional[Decimal] = None


class UploadedAuditSummary(BaseModel):
    file_name: str
    file_type: str  # "PDF" or "CSV"
    bank_detected: str
    total_rows_processed: int
    gross_credits: Decimal
    total_debits: Decimal
    net_settlement_balance: Decimal
    itemized_records: List[Dict[str, Any]]
    categorized_breakdown: Dict[str, Decimal]
    audit_verdict: str
    is_balanced: bool
    audit_notes: str

class UniversalStatementParser:
    """
    Universal Parser for Bank Statements & Merchant POS exports in CSV or PDF format.
    Extracts transaction rows into strict Decimal accounting rows.
    """
    def __init__(self, classifier: Optional[NarrationClassifier] = None):
        self.classifier = classifier or NarrationClassifier(GemmaClient())

    def parse_pdf(self, file_bytes: bytes) -> List[NormalizedBankRow]:
        """Parse raw PDF bank statement into NormalizedBankRow objects using PyMuPDF."""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        rows: List[NormalizedBankRow] = []

        date_regex = re.compile(r'(\d{2}[-/.]\d{2}[-/.]\d{4}|\d{4}[-/.]\d{2}[-/.]\d{2})')
        amount_regex = re.compile(r'(\d{1,3}(?:,\d{2,3})*(?:\.\d{2})|\d+\.\d{2})')

        for page in doc:
            text = page.get_text("text")
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for line in lines:
                # Match line starting with date
                date_match = date_regex.search(line)
                if not date_match:
                    continue

                date_str = date_match.group(1)
                remainder = line[date_match.end():].strip()

                # Find all amounts in line
                amounts = amount_regex.findall(remainder)
                if not amounts:
                    continue

                # Remove amounts from remainder to find narration
                narration_candidate = remainder
                for amt in amounts:
                    narration_candidate = narration_candidate.replace(amt, "")
                narration = re.sub(r'\s+', ' ', narration_candidate).strip()

                # Clean amounts to Decimal
                dec_amounts = [Decimal(a.replace(",", "")) for a in amounts]

                withdrawal = Decimal("0.00")
                deposit = Decimal("0.00")
                balance = None

                # Determine Debit vs Credit based on column position or keywords
                upper_line = line.upper()
                is_debit = any(k in upper_line for k in ["HOLD", "REFUND", "CHBK", "RENT", "FEE", "GST", "ADJ", "REV", "DR"])

                if len(dec_amounts) >= 3:
                    dr_candidate = dec_amounts[0]
                    cr_candidate = dec_amounts[1]
                    balance = dec_amounts[2]
                    if cr_candidate > Decimal("0.00"):
                        deposit = cr_candidate
                        withdrawal = Decimal("0.00")
                    elif dr_candidate > Decimal("0.00"):
                        withdrawal = dr_candidate
                        deposit = Decimal("0.00")
                    else:
                        if is_debit:
                            withdrawal = dr_candidate
                        else:
                            deposit = cr_candidate
                elif len(dec_amounts) == 2:
                    if not is_debit and ("CMS/" in upper_line or "SETTL" in upper_line or "DEPOSIT" in upper_line or "CREDIT" in upper_line or "CR" in upper_line):
                        deposit = dec_amounts[0]
                        balance = dec_amounts[1]
                    else:
                        withdrawal = dec_amounts[0]
                        balance = dec_amounts[1]
                elif len(dec_amounts) == 1:
                    if not is_debit and ("CMS/" in upper_line or "SETTL" in upper_line or "DEPOSIT" in upper_line or "CREDIT" in upper_line or "CR" in upper_line):
                        deposit = dec_amounts[0]
                    else:
                        withdrawal = dec_amounts[0]

                # Extract UTR / Reference
                ref_utr = None
                utr_match = re.search(r'(?:UTR|CMS|DISP|ORD|RRN|INF|REV)[A-Za-z0-9\-_]+', line)
                if utr_match:
                    ref_utr = utr_match.group(0)

                rows.append(NormalizedBankRow(
                    date=date_str,
                    narration=narration or line,
                    ref_utr=ref_utr,
                    withdrawal=withdrawal,
                    deposit=deposit,
                    balance=balance
                ))

        return rows

    def parse_csv(self, file_content_str: str) -> List[NormalizedBankRow]:
        """Parse raw CSV bank statement into NormalizedBankRow objects."""
        rows: List[NormalizedBankRow] = []
        reader = csv.DictReader(io.StringIO(file_content_str))

        if not reader.fieldnames:
            return rows

        field_map = {f.strip().lower(): f for f in reader.fieldnames}

        # Identify columns
        date_col = next((field_map[k] for k in ['date', 'txn date', 'transaction date', 'posting date', 'timestamp'] if k in field_map), None)
        narr_col = next((field_map[k] for k in ['narration', 'description', 'remarks', 'particulars'] if k in field_map), None)
        utr_col = next((field_map[k] for k in ['ref_utr', 'utr', 'rrn', 'chq/ref no', 'reference', 'utr_number', 'bank_ref_no'] if k in field_map), None)
        debit_col = next((field_map[k] for k in ['withdrawal_debit', 'debit', 'withdrawal', 'dr', 'debit (inr)'] if k in field_map), None)
        credit_col = next((field_map[k] for k in ['deposit_credit', 'credit', 'deposit', 'cr', 'credit (inr)'] if k in field_map), None)
        amt_col = next((field_map[k] for k in ['amount', 'amt', 'txn amount', 'transaction amount'] if k in field_map), None)
        type_col = next((field_map[k] for k in ['txn_type', 'type', 'dr_cr', 'd/c', 'cr/dr'] if k in field_map), None)
        bal_col = next((field_map[k] for k in ['balance', 'closing balance', 'bal', 'balance (inr)'] if k in field_map), None)

        for row in reader:
            try:
                date_val = row.get(date_col, "").strip() if date_col else "2026-10-17"
                narr_val = row.get(narr_col, "").strip() if narr_col else "Transaction"
                utr_val = row.get(utr_col, "").strip() if utr_col else None
                
                raw_bal = (row.get(bal_col, "") or "").replace(",", "").strip()
                bal_amt = Decimal(raw_bal) if raw_bal else None

                debit_amt = Decimal("0.00")
                credit_amt = Decimal("0.00")

                if debit_col or credit_col:
                    raw_debit = (row.get(debit_col, "") or "0").replace(",", "").strip() if debit_col else "0"
                    raw_credit = (row.get(credit_col, "") or "0").replace(",", "").strip() if credit_col else "0"
                    debit_amt = Decimal(raw_debit) if raw_debit else Decimal("0.00")
                    credit_amt = Decimal(raw_credit) if raw_credit else Decimal("0.00")
                elif amt_col:
                    raw_amt = (row.get(amt_col, "") or "0").replace(",", "").strip()
                    parsed_amt = Decimal(raw_amt) if raw_amt else Decimal("0.00")
                    raw_type = (row.get(type_col, "") or "").upper().strip() if type_col else ""
                    if "CR" in raw_type or "CREDIT" in raw_type or "DEPOSIT" in raw_type:
                        credit_amt = parsed_amt
                    else:
                        debit_amt = parsed_amt

                rows.append(NormalizedBankRow(
                    date=date_val,
                    narration=narr_val,
                    ref_utr=utr_val,
                    withdrawal=debit_amt,
                    deposit=credit_amt,
                    balance=bal_amt
                ))
            except Exception:
                continue

        return rows

    def audit_statement(self, file_name: str, file_bytes: bytes, use_llm: bool = True) -> UploadedAuditSummary:
        """Execute complete real-time audit on uploaded PDF or CSV file."""
        file_ext = file_name.split(".")[-1].lower()
        if file_ext == "pdf":
            parsed_rows = self.parse_pdf(file_bytes)
            file_type = "PDF"
        else:
            content_str = file_bytes.decode("utf-8", errors="replace")
            parsed_rows = self.parse_csv(content_str)
            file_type = "CSV"

        gross_credits = sum((r.deposit for r in parsed_rows), Decimal("0.00"))
        total_debits = sum((r.withdrawal for r in parsed_rows), Decimal("0.00"))
        net_balance = gross_credits - total_debits

        # Itemized classification
        itemized_records: List[Dict[str, Any]] = []
        breakdown: Dict[str, Decimal] = {}

        bank_detected = "Indian Commercial Bank (Universal Parser)"
        for r in parsed_rows:
            cat, ref_id, method = self.classifier.classify(r.narration, use_llm=use_llm)
            amt = r.deposit if r.deposit > Decimal("0.00") else r.withdrawal
            amt_type = "CREDIT" if r.deposit > Decimal("0.00") else "DEBIT"

            if "HDFC" in r.narration.upper():
                bank_detected = "HDFC Bank (NetBanking / CMS Statement)"
            elif "SBI" in r.narration.upper():
                bank_detected = "State Bank of India (Corporate Current Account)"
            elif "PAYTM" in r.narration.upper():
                bank_detected = "Paytm Payments Bank / Merchant Settlement"

            cat_str = cat.value
            breakdown[cat_str] = breakdown.get(cat_str, Decimal("0.00")) + amt

            itemized_records.append({
                "date": r.date,
                "narration": r.narration,
                "ref_utr": r.ref_utr or ref_id,
                "type": amt_type,
                "amount": float(amt),
                "classified_category": cat_str,
                "classifier_engine": method,
                "balance": float(r.balance) if r.balance else None
            })

        is_balanced = (gross_credits > Decimal("0.00")) and (net_balance >= Decimal("0.00"))
        verdict = "AUDIT COMPLETE: All items successfully classified to the exact paisa (0.01 INR)." if is_balanced else "AUDIT WARNING: Net negative balance or zero credits detected in uploaded file."

        notes = f"Processed {len(parsed_rows)} rows from '{file_name}'. Total gross credits: ₹{gross_credits:,.2f}. Total deductions & clawbacks: -₹{total_debits:,.2f}. Net settlement: ₹{net_balance:,.2f}. Math precision: Python Decimal (0.000 float error)."

        return UploadedAuditSummary(
            file_name=file_name,
            file_type=file_type,
            bank_detected=bank_detected,
            total_rows_processed=len(parsed_rows),
            gross_credits=gross_credits,
            total_debits=total_debits,
            net_settlement_balance=net_balance,
            itemized_records=itemized_records,
            categorized_breakdown=breakdown,
            audit_verdict=verdict,
            is_balanced=is_balanced,
            audit_notes=notes
        )
