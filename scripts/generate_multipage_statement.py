import fitz
import os
import csv
from decimal import Decimal
from zeroresidual.engine.parsers import UniversalStatementParser

def generate():
    # Transactions dataset: 24 realistic Indian merchant transactions
    # 8 per page across 3 pages
    # Total Gross Credits: ₹300,000.00
    # Total Deductions / Debits: ₹19,137.20
    # Net Balance / Settlement: ₹280,862.80
    transactions = [
        # --- PAGE 1: 15-OCT to 16-OCT ---
        {
            "date": "15-10-2026",
            "narration": "CMS/PAYTM/UTR88912001928/MERCHANT_SETTL",
            "ref": "UTR88912001928",
            "dr": "0.00",
            "cr": "35000.00",
            "bal": "85000.00"
        },
        {
            "date": "15-10-2026",
            "narration": "UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-2011/HDFC",
            "ref": "ORD-2011",
            "dr": "1200.00",
            "cr": "0.00",
            "bal": "83800.00"
        },
        {
            "date": "15-10-2026",
            "narration": "POS SERVICE RENTAL 4G IOT SOUNDBOX PAYTM-RENT",
            "ref": "PAYTM-RENT",
            "dr": "423.73",
            "cr": "0.00",
            "bal": "83376.27"
        },
        {
            "date": "15-10-2026",
            "narration": "GST@18% ON DEVICE HARDWARE RENTAL PAYTM-GST",
            "ref": "PAYTM-GST",
            "dr": "76.27",
            "cr": "0.00",
            "bal": "83300.00"
        },
        {
            "date": "15-10-2026",
            "narration": "CMS/BHARATPE/UTR44109281/MERCHANT_SETTL",
            "ref": "UTR44109281",
            "dr": "0.00",
            "cr": "28500.00",
            "bal": "111800.00"
        },
        {
            "date": "15-10-2026",
            "narration": "REV-UPI-REFUND-PAYTM-ORD-2025-SBI",
            "ref": "ORD-2025",
            "dr": "850.00",
            "cr": "0.00",
            "bal": "110950.00"
        },
        {
            "date": "16-10-2026",
            "narration": "CMS/EDC/SWIPE/BATCH-1092/MERCHANT_SETTL",
            "ref": "BATCH-1092",
            "dr": "0.00",
            "cr": "42000.00",
            "bal": "152950.00"
        },
        {
            "date": "16-10-2026",
            "narration": "CHBK-HOLD-DISP-8891-ORD-2045-ICICI-ESCROW",
            "ref": "DISP-8891",
            "dr": "2800.00",
            "cr": "0.00",
            "bal": "150150.00"
        },

        # --- PAGE 2: 16-OCT to 17-OCT ---
        {
            "date": "16-10-2026",
            "narration": "CMS/PHONPE/UTR77210928/MERCHANT_SETTL",
            "ref": "UTR77210928",
            "dr": "0.00",
            "cr": "24000.00",
            "bal": "174150.00"
        },
        {
            "date": "16-10-2026",
            "narration": "HOLD-T+1-NIGHT-SETTLEMENT-ORD-2060-EDC",
            "ref": "ORD-2060",
            "dr": "1500.00",
            "cr": "0.00",
            "bal": "172650.00"
        },
        {
            "date": "17-10-2026",
            "narration": "CMS/PAYTM/UTR99104001882/MERCHANT_SETTL",
            "ref": "UTR99104001882",
            "dr": "0.00",
            "cr": "75000.00",
            "bal": "247650.00"
        },
        {
            "date": "17-10-2026",
            "narration": "UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-2081/HDFC",
            "ref": "ORD-2081",
            "dr": "1850.00",
            "cr": "0.00",
            "bal": "245800.00"
        },
        {
            "date": "17-10-2026",
            "narration": "REV-UPI-REFUND-PAYTM-ORD-2095-SBI",
            "ref": "ORD-2095",
            "dr": "950.00",
            "cr": "0.00",
            "bal": "244850.00"
        },
        {
            "date": "17-10-2026",
            "narration": "CHBK-HOLD-DISP-8841-ORD-2064-ICICI-ESCROW",
            "ref": "DISP-8841",
            "dr": "3500.00",
            "cr": "0.00",
            "bal": "241350.00"
        },
        {
            "date": "17-10-2026",
            "narration": "POS MDR INTERCHANGE FEE ON VISA SWIPE MDR-OCT26",
            "ref": "MDR-OCT26",
            "dr": "540.00",
            "cr": "0.00",
            "bal": "240810.00"
        },
        {
            "date": "17-10-2026",
            "narration": "GST@18% ON CARD MDR INTERCHANGE FEE MDR-GST",
            "ref": "MDR-GST",
            "dr": "97.20",
            "cr": "0.00",
            "bal": "240712.80"
        },

        # --- PAGE 3: 17-OCT to 19-OCT ---
        {
            "date": "17-10-2026",
            "narration": "CMS/GPAY/UTR990214810/MERCHANT_SETTL",
            "ref": "UTR990214810",
            "dr": "0.00",
            "cr": "38000.00",
            "bal": "278712.80"
        },
        {
            "date": "18-10-2026",
            "narration": "HOLD-T+1-NIGHT-SETTLEMENT-ORD-2104-EDC",
            "ref": "ORD-2104",
            "dr": "2100.00",
            "cr": "0.00",
            "bal": "276612.80"
        },
        {
            "date": "18-10-2026",
            "narration": "CMS/PAYTM/UTR9941002819/MERCHANT_SETTL",
            "ref": "UTR9941002819",
            "dr": "0.00",
            "cr": "25000.00",
            "bal": "301612.80"
        },
        {
            "date": "18-10-2026",
            "narration": "CHBK-HOLD-DISP-9012-ORD-2115-HDFC-ESCROW",
            "ref": "DISP-9012",
            "dr": "1650.00",
            "cr": "0.00",
            "bal": "299962.80"
        },
        {
            "date": "19-10-2026",
            "narration": "CMS/BHARATPE/UTR55019283/MERCHANT_SETTL",
            "ref": "UTR55019283",
            "dr": "0.00",
            "cr": "32500.00",
            "bal": "332462.80"
        },
        {
            "date": "19-10-2026",
            "narration": "UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-2130/HDFC",
            "ref": "ORD-2130",
            "dr": "1100.00",
            "cr": "0.00",
            "bal": "331362.80"
        },
        {
            "date": "19-10-2026",
            "narration": "POS SERVICE RENTAL SECOND SOUNDBOX PAYTM-RENT",
            "ref": "PAYTM-RENT",
            "dr": "423.73",
            "cr": "0.00",
            "bal": "330939.07"
        },
        {
            "date": "19-10-2026",
            "narration": "GST@18% ON SECOND SOUNDBOX DEVICE PAYTM-GST",
            "ref": "PAYTM-GST",
            "dr": "76.27",
            "cr": "0.00",
            "bal": "330862.80"
        }
    ]

    # 1. Generate Multi-Page PDF using PyMuPDF
    doc = fitz.open()

    pages_data = [
        transactions[0:8],   # Page 1
        transactions[8:16],  # Page 2
        transactions[16:24]  # Page 3
    ]

    for p_idx, page_txns in enumerate(pages_data, start=1):
        page = doc.new_page(width=612, height=792)  # Standard Letter/A4
        
        # Header banner
        page.draw_rect(fitz.Rect(36, 30, 576, 85), color=(0.06, 0.22, 0.44), fill=(0.06, 0.22, 0.44))
        page.insert_text(fitz.Point(48, 55), "HDFC BANK LIMITED", fontname="helv", fontsize=15, color=(1, 1, 1))
        page.insert_text(fitz.Point(48, 73), "SMART MERCHANT CURRENT ACCOUNT STATEMENT (MULTI-PAGE)", fontname="helv", fontsize=9, color=(0.9, 0.9, 0.9))
        page.insert_text(fitz.Point(480, 55), f"Page {p_idx} of 3", fontname="helv", fontsize=10, color=(1, 1, 1))
        page.insert_text(fitz.Point(450, 73), "PERIOD: 15-19 OCT 2026", fontname="helv", fontsize=8, color=(0.9, 0.9, 0.9))

        # Account Details Box (On every page for authentic banking look)
        page.draw_rect(fitz.Rect(36, 95, 576, 155), color=(0.85, 0.85, 0.85), fill=(0.97, 0.97, 0.97))
        page.insert_text(fitz.Point(48, 112), "Customer Name : SHARMA GENERAL STORE & DAIRY (Prop: Rajesh Sharma)", fontname="helv", fontsize=8.5, color=(0.1, 0.1, 0.1))
        page.insert_text(fitz.Point(48, 126), "Account No    : 50200084920194 | IFSC: HDFC0000060 | MICR: 400240002", fontname="helv", fontsize=8.5, color=(0.1, 0.1, 0.1))
        page.insert_text(fitz.Point(48, 140), "Branch        : Fort Business Banking Branch, Mumbai - 400001 | Currency: INR", fontname="helv", fontsize=8.5, color=(0.1, 0.1, 0.1))
        page.insert_text(fitz.Point(410, 112), "Opening Balance: Rs 50,000.00", fontname="helv", fontsize=8.5, color=(0.1, 0.1, 0.1))
        page.insert_text(fitz.Point(410, 126), "Account Type   : Current Account", fontname="helv", fontsize=8.5, color=(0.1, 0.1, 0.1))
        page.insert_text(fitz.Point(410, 140), "Status         : KYC VERIFIED ACTIVE", fontname="helv", fontsize=8.5, color=(0.0, 0.5, 0.2))

        # Table Header Bar
        table_top = 175
        page.draw_rect(fitz.Rect(36, table_top, 576, table_top + 22), color=(0.2, 0.2, 0.2), fill=(0.92, 0.93, 0.95))
        # Header titles formatted exactly with courier monospaced column positions
        header_text = f"{'Date':<11} {'Narration / Merchant Description':<46} {'Ref / Chq No':<16} {'Withdrawal':>10} {'Deposit':>10} {'Balance':>10}"
        page.insert_text(fitz.Point(42, table_top + 15), header_text, fontname="cour", fontsize=8, color=(0.1, 0.1, 0.1))

        # Draw Table Rows
        row_y = table_top + 38
        for t in page_txns:
            # Alternating background row tint
            page.draw_rect(fitz.Rect(36, row_y - 12, 576, row_y + 8), color=(0.93, 0.93, 0.93), fill=(0.99, 0.99, 0.99))
            
            # Formatted monospaced line that PyMuPDF extracts as a single coherent line
            line_str = f"{t['date']:<11} {t['narration']:<46} {t['ref']:<16} {t['dr']:>10} {t['cr']:>10} {t['bal']:>10}"
            page.insert_text(fitz.Point(42, row_y), line_str, fontname="cour", fontsize=8, color=(0.05, 0.05, 0.05))
            row_y += 24

        # Page-specific footers
        if p_idx == 3:
            # Summary Box on Page 3
            box_top = row_y + 15
            page.draw_rect(fitz.Rect(36, box_top, 576, box_top + 105), color=(0.06, 0.22, 0.44), fill=(0.96, 0.97, 0.99))
            page.insert_text(fitz.Point(48, box_top + 22), "AUDIT & STATEMENT RECONCILIATION SUMMARY (PAGES 1-3 CONSOLIDATED)", fontname="helv", fontsize=9.5, color=(0.06, 0.22, 0.44))
            page.insert_text(fitz.Point(48, box_top + 42), "Total Gross Merchant Credits (UPI/Cards/CMS) : Rs 300,000.00 (8 Batches)", fontname="cour", fontsize=8.5, color=(0, 0.5, 0))
            page.insert_text(fitz.Point(48, box_top + 58), "Total Deductions & Merchant Clawbacks        : -Rs 19,137.20 (16 Adjustments)", fontname="cour", fontsize=8.5, color=(0.8, 0.1, 0))
            page.insert_text(fitz.Point(48, box_top + 74), "Net Merchant Settlement Credits Received    : Rs 280,862.80", fontname="cour", fontsize=8.5, color=(0.06, 0.22, 0.44))
            page.insert_text(fitz.Point(48, box_top + 90), "Closing Book Balance as on 19-OCT-2026      : Rs 330,862.80 [Opening Rs 50k + Net Rs 280,862.80]", fontname="cour", fontsize=8.5, color=(0.1, 0.1, 0.1))

            # Bank Seal
            seal_y = box_top + 130
            page.insert_text(fitz.Point(48, seal_y), "Verified by: Core Banking System (HDFC Finacle 10.x)", fontname="helv", fontsize=8, color=(0.4, 0.4, 0.4))
            page.insert_text(fitz.Point(48, seal_y + 14), "Digital Signature SHA-256: 7f8a3c9b1e2d4a5c6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d", fontname="helv", fontsize=7, color=(0.5, 0.5, 0.5))
            page.insert_text(fitz.Point(48, seal_y + 26), "This is a computer generated multi-page account statement. No physical signature required.", fontname="helv", fontsize=7.5, color=(0.4, 0.4, 0.4))
        else:
            page.insert_text(fitz.Point(450, row_y + 30), f"Continued on Page {p_idx + 1}...", fontname="helv", fontsize=8.5, color=(0.4, 0.4, 0.4))

    # Save PDF to target destinations
    pdf_paths = [
        "data/sample_merchant_hdfc_statement.pdf",
        "frontend/public/sample_merchant_hdfc_statement.pdf",
        "frontend/public/sample_hdfc_statement.pdf"
    ]
    for p in pdf_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        doc.save(p)
        print(f"✓ Saved {p} ({len(doc)} pages)")

    # 2. Generate Matching Multi-row CSV
    csv_paths = [
        "data/sample_merchant_statement.csv",
        "frontend/public/sample_merchant_statement.csv",
        "frontend/public/bank_settlement.csv"
    ]
    for cp in csv_paths:
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        with open(cp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "narration", "chq_ref_no", "withdrawal", "deposit", "balance"])
            writer.writeheader()
            for t in transactions:
                writer.writerow({
                    "date": t["date"],
                    "narration": t["narration"],
                    "chq_ref_no": t["ref"],
                    "withdrawal": t["dr"],
                    "deposit": t["cr"],
                    "balance": t["bal"]
                })
        print(f"✓ Saved {cp} ({len(transactions)} rows)")

    # 3. Test verification with UniversalStatementParser
    parser = UniversalStatementParser()
    with open("data/sample_merchant_hdfc_statement.pdf", "rb") as f:
        pdf_bytes = f.read()
    summary = parser.audit_statement("sample_merchant_hdfc_statement.pdf", pdf_bytes, use_llm=False)
    
    print("\n--- AUDIT VERIFICATION RESULTS ---")
    print(f"Total Rows Processed : {summary.total_rows_processed} / 24")
    print(f"Gross Credits        : ₹{summary.gross_credits:,.2f}")
    print(f"Total Debits         : ₹{summary.total_debits:,.2f}")
    print(f"Net Settlement       : ₹{summary.net_settlement_balance:,.2f}")
    print(f"Breakdown            : {summary.categorized_breakdown}")
    print(f"Is Balanced          : {summary.is_balanced}")
    print(f"Verdict              : {summary.audit_verdict}")

if __name__ == "__main__":
    generate()
