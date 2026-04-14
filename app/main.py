from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from google.oauth2 import service_account
from clfl_core_library import DriveManager
import os

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS',
    os.path.join(os.path.dirname(__file__), '..', 'secrets', 'shipment-invoice-extractor-1300acac7dd8.json')
)
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', 'shipment-invoice-extractor')
GOOGLE_CLOUD_LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES)
drive_manager = DriveManager(credentials)

app = FastAPI()

class FileData(BaseModel):
    base64_content: str
    mime_type: str
    filename: str


@app.get("/")
async def health_check():
    return {"status": "healthy"}

@app.get('/test-auth')
async def test_auth():
    return {
        "project_id": credentials.project_id,
        "service_account_email": credentials.service_account_email,
        "scopes": list(credentials.scopes) if credentials.scopes else None,
    }

@app.post("/classify")
async def classify_document(file: FileData):
    return { 
        "received_filename": file.filename,
        "mime_type": file.mime_type,
        "base64_length": len(file.base64_content)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)