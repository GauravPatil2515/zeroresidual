from decimal import Decimal
from zeroresidual.engine.types import FactSheet
from zeroresidual.engine.number_guard import NumberGuard

def test_number_guard_accepts_verified_numbers():
    facts = FactSheet(
        gross_pos=Decimal("50000.00"),
        bank_received=Decimal("43000.00"),
        refund_total=Decimal("2400.00"),
        chargeback_total=Decimal("3100.00"),
        cutoff_total=Decimal("1000.00"),
        soundbox_fee_total=Decimal("423.73"),
        soundbox_gst_total=Decimal("76.27"),
        calculated_payout=Decimal("43000.00"),
        residual=Decimal("0.00")
    )

    clean_text = "Gross sales were ₹50,000.00 and bank received ₹43,000.00 with ₹2,400.00 refunds."
    is_valid, offending = NumberGuard.validate_text(clean_text, facts)
    assert is_valid is True
    assert len(offending) == 0

def test_number_guard_rejects_hallucinated_figures():
    facts = FactSheet(
        gross_pos=Decimal("50000.00"),
        bank_received=Decimal("43000.00"),
        refund_total=Decimal("2400.00"),
        chargeback_total=Decimal("3100.00"),
        cutoff_total=Decimal("1000.00"),
        soundbox_fee_total=Decimal("423.73"),
        soundbox_gst_total=Decimal("76.27"),
        calculated_payout=Decimal("43000.00"),
        residual=Decimal("0.00")
    )

    hallucinated_text = "The bank withheld ₹15,420 for unexplained processing fees."
    is_valid, offending = NumberGuard.validate_text(hallucinated_text, facts)
    assert is_valid is False
    assert "15420" in offending
