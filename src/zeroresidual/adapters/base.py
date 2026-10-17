from abc import ABC, abstractmethod
from typing import Optional, Tuple
from zeroresidual.engine.types import DeductionCategory

class BaseBankAdapter(ABC):
    """
    Open-source interface for parsing Indian bank settlement narrations.
    Allows community developers to add any bank adapter in ~20 lines of code.
    """
    bank_code: str = "GENERIC"

    @abstractmethod
    def can_handle(self, narration: str) -> bool:
        """Returns True if this adapter recognizes the bank statement format."""
        pass

    @abstractmethod
    def parse_narration(self, narration: str) -> Tuple[DeductionCategory, Optional[str]]:
        """
        Parses raw bank narration string into:
        (DeductionCategory, reference_id_or_order_id)
        """
        pass
