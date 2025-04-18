from fastapi import FastAPI
from app.endpoints.csv_upload import router as csv_upload_router
from app.endpoints.validate_dataset import router as validate_dataset_router

app = FastAPI(
    title="Data Processing API",
    description="Uploads CSV files and processes them using validation rules.",
    version="1.0"
)

@app.get("/")
async def index():
    return {"message": "Welcome to the Data Processing API. Visit /docs for API documentation."}

app.include_router(csv_upload_router)
app.include_router(validate_dataset_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
