import os
from decimal import Decimal
from zeroresidual.engine.recon import ReconciliationEngine

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def test_scenario_1_exact_tieout_to_the_paisa():
    """Property test: Sum of tagged deductions + calculated payout == Gross POS sales down to 0.01 paisa."""
    engine = ReconciliationEngine()
    p1 = os.path.join(DATA_DIR, "scenario_1_tieout", "pos_orders.csv")
    p2 = os.path.join(DATA_DIR, "scenario_1_tieout", "webhooks.json")
    p3 = os.path.join(DATA_DIR, "scenario_1_tieout", "bank_settlement.csv")

    res = engine.reconcile(p1, p2, p3, use_llm=False)

    assert res.gross_pos_sales == Decimal("50000.00")
    assert res.bank_received_payout == Decimal("43000.00")
    assert res.total_deductions == Decimal("7000.00")
    assert res.expected_payout == Decimal("43000.00")
    assert res.residual == Decimal("0.00")
    assert res.is_reconciled is True
    assert res.exit_code == 0

    # Invariant: Gross - Deductions == Payout
    assert (res.gross_pos_sales - res.total_deductions) == res.expected_payout

def test_scenario_2_flags_unexplained_residual():
    """Asserts that missing ₹212.00 is tagged as UNEXPLAINED without guessing."""
    engine = ReconciliationEngine()
    p1 = os.path.join(DATA_DIR, "scenario_2_unexplained", "pos_orders.csv")
    p2 = os.path.join(DATA_DIR, "scenario_2_unexplained", "webhooks.json")
    p3 = os.path.join(DATA_DIR, "scenario_2_unexplained", "bank_settlement.csv")

    res = engine.reconcile(p1, p2, p3, use_llm=False)

    assert res.gross_pos_sales == Decimal("50000.00")
    assert res.bank_received_payout == Decimal("42788.00")
    assert res.residual == Decimal("-212.00")
    assert abs(res.residual) == Decimal("212.00")
    assert res.is_reconciled is False
    assert res.exit_code == 1
    assert "UNEXPLAINED RESIDUAL" in res.explanation_en
