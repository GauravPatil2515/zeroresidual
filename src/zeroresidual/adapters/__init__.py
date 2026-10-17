from typing import List
from zeroresidual.adapters.base import BaseBankAdapter
from zeroresidual.adapters.hdfc import HDFCBankAdapter
from zeroresidual.adapters.sbi import SBIBankAdapter
from zeroresidual.adapters.paytm import PaytmSoundboxAdapter

DEFAULT_ADAPTERS: List[BaseBankAdapter] = [
    PaytmSoundboxAdapter(),
    HDFCBankAdapter(),
    SBIBankAdapter(),
]

def get_registered_adapters() -> List[BaseBankAdapter]:
    return DEFAULT_ADAPTERS
