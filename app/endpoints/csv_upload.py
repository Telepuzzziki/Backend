from fastapi import APIRouter, UploadFile, File, HTTPException
import csv
import io
from typing import List, Dict

router = APIRouter()


class CsvProcessor:
    """Class responsible for processing CSV files."""
    async def process_csv(self, file: UploadFile) -> List[Dict[str, str]]:
        if not file.filename.endswith('.csv'):
            raise ValueError("Only CSV files with .csv extension are allowed.")
        try:
            contents = await file.read()
            decoded = contents.decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            data = [row for row in reader]
            return data
        except Exception as e:
            raise ValueError("Failed to process CSV file.") from e
        
        return 


csv_processor = CsvProcessor()


@router.post("/csv_upload", summary="Endpoint to upload and process CSV files")
async def csv_upload(file: UploadFile = File(...)):
    """
    Upload a CSV file and process its contents.

    Returns:
        dict: A dictionary with the key 'data' containing the CSV parsed rows.
    """
    try:
        data = await csv_processor.process_csv(file)
        return {"success": True, "data": data}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) 
    
    return 
