from fastapi import APIRouter, UploadFile, File, HTTPException
import io
import pandas as pd
from app.core.validator import CsvValidator, is_invalid_date, is_invalid_ipv4, is_invalid_positive_numeric, remove_microseconds_regex_inplace

router = APIRouter()

@router.post("/validate_dataset", summary="Endpoint to validate any dataset (CSV) using default rules")
async def validate_dataset(file: UploadFile = File(...)):
    """
    Accepts a CSV file, applies default validation rules, and returns the modified dataset as JSON.
    Default rules applied:
      - If 'created_on' column exists, validate using is_invalid_date
      - If 'updated_on' column exists, validate using is_invalid_date
      - If 'ip' column exists, validate using is_invalid_ipv4
      - If 'cpu_cores' column exists, validate using is_invalid_positive_numeric
      - If 'cpu_freq' column exists, validate using is_invalid_positive_numeric
      - If 'ram' column exists, validate using is_invalid_positive_numeric
      - If 'total_volume' column exists, validate using is_invalid_positive_numeric
      - Remove microseconds from 'created_on' and 'updated_on' columns
      - Only works with CSV files and ISO 8601 date format
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    try:
        file_contents = await file.read()
        df = pd.read_csv(io.StringIO(file_contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to read CSV file.")
    
    rules = {
        is_invalid_ipv4: ['ip'],
        is_invalid_positive_numeric: ['cpu_cores', 'cpu_freq', 'ram', 'total_volume'],
        is_invalid_date: ['created_on', 'updated_on']
    }
    remove_microseconds_regex_inplace(df, ['created_on', 'updated_on'])
    
    validator = CsvValidator(df)
    modified_df = validator.validate(rules)
    
    return {"success": True, "data": modified_df.to_json(orient='records')} 
