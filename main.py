from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import os
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'secrets', 'shipment-invoice-extractor-1300acac7dd8.json')
SCOPES = ['https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/spreadsheets']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

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