from zeroresidual.adapters.hdfc import HDFCBankAdapter
from zeroresidual.adapters.sbi import SBIBankAdapter
from zeroresidual.adapters.paytm import PaytmSoundboxAdapter
from zeroresidual.engine.types import DeductionCategory

def test_hdfc_adapter_parses_refund_and_dispute():
    adapter = HDFCBankAdapter()
    assert adapter.can_handle("UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-1011/HDFC") is True
    cat, order_id = adapter.parse_narration("UPI/CR/99210/PAYTM_REFUND_ADJ/ORD-1011/HDFC")
    assert cat == DeductionCategory.REFUND
    assert order_id == "ORD-1011"

def test_sbi_adapter_parses_reversal():
    adapter = SBIBankAdapter()
    assert adapter.can_handle("REV-UPI-REFUND-PAYTM-ORD-1025-SBI") is True
    cat, order_id = adapter.parse_narration("REV-UPI-REFUND-PAYTM-ORD-1025-SBI")
    assert cat == DeductionCategory.REFUND
    assert order_id == "ORD-1025"

def test_paytm_adapter_parses_soundbox_fees():
    adapter = PaytmSoundboxAdapter()
    assert adapter.can_handle("PAYTM-SNDBOX-RENTAL-OCT26-DEVICE-SN7719") is True
    cat, _ = adapter.parse_narration("PAYTM-SNDBOX-RENTAL-OCT26-DEVICE-SN7719")
    assert cat == DeductionCategory.SOUNDBOX_FEE

    assert adapter.can_handle("GST@18%-ON-PAYTM-SOUNDBOX-CHARGES-HSN9983") is True
    cat2, _ = adapter.parse_narration("GST@18%-ON-PAYTM-SOUNDBOX-CHARGES-HSN9983")
    assert cat2 == DeductionCategory.SOUNDBOX_GST
