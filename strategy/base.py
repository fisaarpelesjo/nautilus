from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradeSignal:
    signal: Signal
    price: float
    reason: str

class BaseStrategy(ABC):
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        pass
