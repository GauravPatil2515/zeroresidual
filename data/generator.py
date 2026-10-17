import csv
import json
import os
from decimal import Decimal
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_scenario_1():
    """
    Scenario 1: Perfect Tie-Out
    - Gross POS Sales: ₹50,000.00 (50 transactions across the day)
    - Bank Received: ₹43,000.00
    - Deductions:
        * Refund: ₹2,400.00 (ORD-1011: ₹1,400, ORD-1025: ₹1,000)
        * Chargeback Hold: ₹3,100.00 (ORD-1008, Dispute #DISP-992)
        * T+1 Cutoff Delayed: ₹1,000.00 (ORD-1048: ₹300, ORD-1049: ₹450, ORD-1050: ₹250 after 23:00 IST)
        * Soundbox Rental: ₹423.73 + 18% GST ₹76.27 = ₹500.00
    - Total Deductions: ₹7,000.00
    - Calculated Payout: ₹43,000.00
    - Residual: ₹0.00
    """
    target_dir = os.path.join(BASE_DIR, "scenario_1_tieout")
    os.makedirs(target_dir, exist_ok=True)

    # 1. POS Orders CSV (50 orders total)
    pos_orders = []
    # Standard 44 settled orders: sum = 50,000 - 2400 - 3100 - 1000 = 43,500
    # Let's create orders summing to ₹50,000
    amounts = [
        # Regular successful orders (will settle today, sum = 42,500.00)
        800, 1200, 500, 1500, 950, 750, 1100, 450, 650, 1350,
        900, 1600, 700, 850, 1250, 1400, 600, 1150, 1300, 750,
        950, 1050, 850, 1200, 1100, 900, 1500, 800, 700, 1300,
        950, 1050, 1250, 850, 900, 1150, 1400, 750, 850, 1300,
        950, 1100, 200, 700, # reduced by 1000 to make gross exactly 50,000.00
    ] # 44 items. Sum of these = 42,500

    order_idx = 1
    for amt in amounts:
        order_id = f"ORD-{1000 + order_idx:04d}"
        pos_orders.append({
            "order_id": order_id,
            "amount": f"{amt:.2f}",
            "timestamp": "2026-10-17 14:15:00",
            "status": "SUCCESS",
            "payment_method": "UPI",
            "customer_vpa": f"customer{order_idx}@paytm"
        })
        order_idx += 1

    # Order 45 & 46: Refunds (₹1,400 + ₹1,000 = ₹2,400)
    pos_orders.append({
        "order_id": "ORD-1011",
        "amount": "1400.00",
        "timestamp": "2026-10-17 11:30:00",
        "status": "REFUNDED",
        "payment_method": "UPI",
        "customer_vpa": "rohit.sharma@okhdfcbank"
    })
    pos_orders.append({
        "order_id": "ORD-1025",
        "amount": "1000.00",
        "timestamp": "2026-10-17 12:45:00",
        "status": "REFUNDED",
        "payment_method": "UPI",
        "customer_vpa": "priya.nair@oksbi"
    })

    # Order 47: Chargeback hold (₹3,100)
    pos_orders.append({
        "order_id": "ORD-1008",
        "amount": "3100.00",
        "timestamp": "2026-10-17 10:15:00",
        "status": "SUCCESS",
        "payment_method": "UPI",
        "customer_vpa": "vikram.patel@icici"
    })

    # Order 48, 49, 50: T+1 Cutoff Delayed (placed after 23:00 IST cutoff, ₹300 + ₹450 + ₹250 = ₹1,000)
    pos_orders.append({
        "order_id": "ORD-1048",
        "amount": "300.00",
        "timestamp": "2026-10-17 23:14:22",
        "status": "SUCCESS",
        "payment_method": "UPI",
        "customer_vpa": "ananya.sen@paytm"
    })
    pos_orders.append({
        "order_id": "ORD-1049",
        "amount": "450.00",
        "timestamp": "2026-10-17 23:28:40",
        "status": "SUCCESS",
        "payment_method": "UPI",
        "customer_vpa": "karthik.r@axisbank"
    })
    pos_orders.append({
        "order_id": "ORD-1050",
        "amount": "250.00",
        "timestamp": "2026-10-17 23:45:10",
        "status": "SUCCESS",
        "payment_method": "UPI",
        "customer_vpa": "dev.gupta@okicici"
    })

    # Write POS orders CSV
    with open(os.path.join(target_dir, "pos_orders.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "amount", "timestamp", "status", "payment_method", "customer_vpa"])
        writer.writeheader()
        writer.writerows(pos_orders)

    # 2. Webhooks Log JSON
    webhooks = []
    for order in pos_orders:
        oid = order["order_id"]
        amt = order["amount"]
        if oid in ["ORD-1011", "ORD-1025"]:
            webhooks.append({
                "event_id": f"EVT-{oid}-PAY",
                "order_id": oid,
                "paytm_txn_id": f"TXN-PTM-{oid}",
                "event_type": "PAYMENT_SUCCESS",
                "amount": amt,
                "status": "SUCCESS",
                "timestamp": order["timestamp"]
            })
            webhooks.append({
                "event_id": f"EVT-{oid}-REF",
                "order_id": oid,
                "paytm_txn_id": f"REF-PTM-{oid}",
                "event_type": "REFUND_SUCCESS",
                "amount": amt,
                "status": "REFUNDED",
                "timestamp": "2026-10-17 18:00:00"
            })
        elif oid == "ORD-1008":
            webhooks.append({
                "event_id": f"EVT-{oid}-PAY",
                "order_id": oid,
                "paytm_txn_id": f"TXN-PTM-{oid}",
                "event_type": "PAYMENT_SUCCESS",
                "amount": amt,
                "status": "SUCCESS",
                "timestamp": order["timestamp"]
            })
            webhooks.append({
                "event_id": f"EVT-{oid}-CHBK",
                "order_id": oid,
                "paytm_txn_id": f"TXN-PTM-{oid}",
                "event_type": "CHARGEBACK_RAISED",
                "amount": amt,
                "status": "HELD_IN_ESCROW",
                "timestamp": "2026-10-17 19:30:00",
                "dispute_id": "DISP-992",
                "reason": "Customer reported unauthorized UPI transaction via bank"
            })
        else:
            webhooks.append({
                "event_id": f"EVT-{oid}-PAY",
                "order_id": oid,
                "paytm_txn_id": f"TXN-PTM-{oid}",
                "event_type": "PAYMENT_SUCCESS",
                "amount": amt,
                "status": "SUCCESS",
                "timestamp": order["timestamp"]
            })

    with open(os.path.join(target_dir, "webhooks.json"), "w") as f:
        json.dump(webhooks, f, indent=2)

    # 3. Bank Settlement CSV (with realistic unstandardized bank narrations)
    bank_records = [
        # Net Settlement Credit to Merchant Account
        {
            "bank_ref_no": "BNK-CR-88912",
            "utr_number": "PAYTM88912001928",
            "amount": "43000.00",
            "txn_type": "CR",
            "narration": "NEFT-PAYTM-SETTL-OCT17-MID7721-UTR88912",
            "timestamp": "2026-10-18 06:30:00"
        },
        # Deductions & Adjustments noted in bank settlement advice:
        {
            "bank_ref_no": "BNK-ADJ-REF1",
            "utr_number": "REF8891201",
            "amount": "1400.00",
            "txn_type": "DR",
            "narration": "UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-1011/HDFC",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-ADJ-REF2",
            "utr_number": "REF8891202",
            "amount": "1000.00",
            "txn_type": "DR",
            "narration": "REV-UPI-REFUND-PAYTM-ORD-1025-SBI",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-ADJ-CHBK",
            "utr_number": "CHBK8891203",
            "amount": "3100.00",
            "txn_type": "DR",
            "narration": "CHBK-HOLD-DISP-992-ORD-1008-ICICI-ESCROW",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-FEE-SNDBOX",
            "utr_number": "FEE8891204",
            "amount": "423.73",
            "txn_type": "DR",
            "narration": "PAYTM-SNDBOX-RENTAL-OCT26-DEVICE-SN7719",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-FEE-GST",
            "utr_number": "GST8891205",
            "amount": "76.27",
            "txn_type": "DR",
            "narration": "GST@18%-ON-PAYTM-SOUNDBOX-CHARGES-HSN9983",
            "timestamp": "2026-10-18 06:30:00"
        }
    ]

    with open(os.path.join(target_dir, "bank_settlement.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["bank_ref_no", "utr_number", "amount", "txn_type", "narration", "timestamp"])
        writer.writeheader()
        writer.writerows(bank_records)

    print("✓ Scenario 1 (Tie-Out) successfully created.")

def generate_scenario_2():
    """
    Scenario 2: Unexplained Discrepancy (The Honest Residual)
    - Gross POS: ₹50,000.00
    - Bank Received: ₹42,788.00 (Short by ₹212.00)
    - Residual: ₹212.00
    - System flags 'UNEXPLAINED RESIDUAL', refuses to guess, and exits with code 1.
    """
    target_dir = os.path.join(BASE_DIR, "scenario_2_unexplained")
    os.makedirs(target_dir, exist_ok=True)

    # Copy POS and webhooks from scenario 1
    src_dir = os.path.join(BASE_DIR, "scenario_1_tieout")
    with open(os.path.join(src_dir, "pos_orders.csv"), "r") as src, open(os.path.join(target_dir, "pos_orders.csv"), "w") as dst:
        dst.write(src.read())

    with open(os.path.join(src_dir, "webhooks.json"), "r") as src, open(os.path.join(target_dir, "webhooks.json"), "w") as dst:
        dst.write(src.read())

    # Bank settlement has ₹42,788.00 instead of ₹43,000.00
    bank_records = [
        {
            "bank_ref_no": "BNK-CR-99104",
            "utr_number": "PAYTM99104001882",
            "amount": "42788.00",  # EXACTLY ₹212.00 LESS!
            "txn_type": "CR",
            "narration": "NEFT-PAYTM-SETTL-OCT17-MID7721-UTR99104",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-ADJ-REF1",
            "utr_number": "REF8891201",
            "amount": "1400.00",
            "txn_type": "DR",
            "narration": "UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-1011/HDFC",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-ADJ-REF2",
            "utr_number": "REF8891202",
            "amount": "1000.00",
            "txn_type": "DR",
            "narration": "REV-UPI-REFUND-PAYTM-ORD-1025-SBI",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-ADJ-CHBK",
            "utr_number": "CHBK8891203",
            "amount": "3100.00",
            "txn_type": "DR",
            "narration": "CHBK-HOLD-DISP-992-ORD-1008-ICICI-ESCROW",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-FEE-SNDBOX",
            "utr_number": "FEE8891204",
            "amount": "423.73",
            "txn_type": "DR",
            "narration": "PAYTM-SNDBOX-RENTAL-OCT26-DEVICE-SN7719",
            "timestamp": "2026-10-18 06:30:00"
        },
        {
            "bank_ref_no": "BNK-FEE-GST",
            "utr_number": "GST8891205",
            "amount": "76.27",
            "txn_type": "DR",
            "narration": "GST@18%-ON-PAYTM-SOUNDBOX-CHARGES-HSN9983",
            "timestamp": "2026-10-18 06:30:00"
        }
    ]

    with open(os.path.join(target_dir, "bank_settlement.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["bank_ref_no", "utr_number", "amount", "txn_type", "narration", "timestamp"])
        writer.writeheader()
        writer.writerows(bank_records)

    print("✓ Scenario 2 (Unexplained Residual ₹212.00) successfully created.")

if __name__ == "__main__":
    generate_scenario_1()
    generate_scenario_2()
