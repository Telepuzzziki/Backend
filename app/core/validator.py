import re
import ipaddress
import pandas as pd
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from .interfaces import ValidatorInterface


@dataclass
class ModificationRecord:
    index: Any
    original_value: Any
    replaced_value: Any
    validator: str


def is_invalid_date(series: pd.Series) -> pd.Series:
    pattern = r"^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) ([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"
    regex = re.compile(pattern)
    invalid_mask = []
    for item in series:
        is_invalid = True
        if pd.isna(item):
            is_invalid = False
        elif isinstance(item, str):
            if regex.fullmatch(item.strip()):
                is_invalid = False
        invalid_mask.append(is_invalid)
    final_mask = pd.Series(invalid_mask, index=series.index)
    return final_mask & series.notna()


def remove_microseconds_regex_inplace(df: pd.DataFrame, columns: List[str]) -> None:
    """
    Removes microseconds (dot + digits at the end) from strings in specified columns in-place.
    """
    regex_pattern = r"\.\d+$"
    for col in columns:
        if col in df.columns:
            try:
                df[col] = df[col].fillna('').astype(str).str.replace(regex_pattern, "", regex=True)
            except Exception as e:
                print(f"  ERROR processing column '{col}': {e}")
        else:
            print(f"  Warning: Column '{col}' not found in DataFrame.")
    return


def is_invalid_ipv4(series: pd.Series) -> pd.Series:
    """Checks for values that are not valid IPv4 addresses."""
    invalid_mask_list = []
    for item in series:
        is_invalid = True
        if pd.notna(item) and isinstance(item, str):
            try:
                ipaddress.IPv4Address(item.strip())
                is_invalid = False
            except ValueError:
                is_invalid = True
        if pd.isna(item):
            invalid_mask_list.append(False)
        else:
            invalid_mask_list.append(is_invalid)
    return pd.Series(invalid_mask_list, index=series.index)


def is_invalid_positive_numeric(series: pd.Series) -> pd.Series:
    """Checks for values that are not numbers strictly greater than 0."""
    numeric_vals = pd.to_numeric(series, errors='coerce')
    invalid_mask = ((numeric_vals.isna() & series.notna()) |
                    (numeric_vals.notna() & (numeric_vals <= 0)))
    return invalid_mask


def apply_validations_inplace(
    df: pd.DataFrame,
    rules: Dict[Callable[[pd.Series], pd.Series], List[str]],
    replacement_value: Any = ' '
) -> Dict[str, List[ModificationRecord]]:
    """
    Applies validation rules in-place on the DataFrame and returns a detailed modifications report.

    Args:
        df: The DataFrame to validate.
        rules: A dictionary mapping validation functions to a list of column names to validate.
        replacement_value: The value to replace invalid entries with.

    Returns:
        A dictionary where keys are column names and values are lists of ModificationRecord detailing changes.
    """
    modifications_report: Dict[str, List[ModificationRecord]] = {}

    if not df.index.is_unique:
        print("WARNING: DataFrame index is not unique! This could cause issues.")

    for validator_func, columns_to_validate in rules.items():
        validator_name = validator_func.__name__ if hasattr(validator_func, '__name__') else str(validator_func)
        if validator_name == "<lambda>":
            validator_name = f"lambda_{hex(id(validator_func))}"

        for col_name in columns_to_validate:
            if col_name not in df.columns:
                print(f"Warning: Column '{col_name}' specified for '{validator_name}' not found. Skipping.")
                continue

            series_to_validate = df[col_name]

            try:
                invalid_mask = validator_func(series_to_validate)
                if not df.index.equals(invalid_mask.index):
                    print(f"  CRITICAL WARNING [{col_name}]: DataFrame index and mask index DO NOT MATCH for validator '{validator_name}'!")
                    if len(df.index) == len(invalid_mask.index):
                        print("  Attempting to reindex mask...")
                        try:
                            invalid_mask = invalid_mask.reindex(df.index)
                        except Exception as reindex_e:
                            print(f"  ERROR: Failed to reindex mask: {reindex_e}. Skipping column.")
                            continue
                    else:
                        print(f"  ERROR: Length mismatch (DF: {len(df.index)}, Mask: {len(invalid_mask.index)}). Skipping column.")
                        continue
                invalid_indices = df.index[invalid_mask].tolist()
            except Exception as e:
                print(f"  ERROR applying validator '{validator_name}' or getting indices for column '{col_name}': {e}")
                continue 

            if invalid_indices:
                print(f"  -> Validator '{validator_name}' found {len(invalid_indices)} invalid entries for '{col_name}'. Recording...")
                if col_name not in modifications_report:
                    modifications_report[col_name] = []

                for idx in invalid_indices:
                    try:
                        original_value = df.loc[idx, col_name]
                        record = ModificationRecord(
                            index=idx,
                            original_value=original_value,
                            replaced_value=replacement_value,
                            validator=validator_name
                        )
                        modifications_report[col_name].append(record)
                    except KeyError:
                        print(f"  Warning: Index {idx} not found during reporting for column '{col_name}'. Skipping record.")
                    except Exception as report_e:
                        print(f"  Error creating report record for index {idx}, col '{col_name}': {report_e}")

                try:
                    df.loc[invalid_indices, col_name] = replacement_value
                except Exception as replace_e:
                    print(f"  ERROR during replacement in column '{col_name}' by validator '{validator_name}': {replace_e}")

    return modifications_report


class CsvValidator(ValidatorInterface):
    """
    Concrete implementation of ValidatorInterface for CSV files represented as a pandas DataFrame.
    """
    def __init__(self, dataframe: pd.DataFrame):
        self._dataframe = dataframe

    def validate(self, rules: Dict[Callable[[pd.Series], pd.Series], List[str]], replacement_value: Any = ' ') -> pd.DataFrame:
        """
        Applies the validation rules to the internal DataFrame and returns the modified DataFrame.
        """
        apply_validations_inplace(self._dataframe, rules, replacement_value)
        return self._dataframe

    def get_dataframe(self) -> pd.DataFrame:
        """Returns the current state of the DataFrame."""
        return self._dataframe

    def to_json(self) -> str:
        """Serializes the DataFrame to a JSON string (records orientation)."""
        return self._dataframe.to_json(orient='records')

    def __repr__(self) -> str:
        return f"CsvValidator(dataframe_shape={self._dataframe.shape})" 
