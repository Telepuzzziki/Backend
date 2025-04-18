from typing import Any, Dict, List, Callable
import pandas as pd


class ValidatorInterface:
    """
    An interface for validating a pandas DataFrame.
    Subclasses should implement the validate method.
    """
    def validate(self, rules: Dict[Callable[[pd.Series], pd.Series], List[str]], replacement_value: Any = ' ') -> Dict[str, List[Any]]:
        raise NotImplementedError("Subclasses should implement this method") 