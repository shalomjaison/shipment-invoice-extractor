from clfl_core_library import DriveManager, extract_year_from_shipment, SheetsManager
from google.genai import types
from google.oauth2 import service_account
from google import genai
import base64
import os
import json

_drive_manager = None
_sheets_manager = None
_genai_client = None

def get_credentials():
    """Shared credentials loader"""
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    return service_account.Credentials.from_service_account_file(creds_path)

def get_drive_manager() -> DriveManager:
    global _drive_manager
    if _drive_manager is None:
        _drive_manager = DriveManager(get_credentials())
    return _drive_manager

def get_sheets_manager() -> SheetsManager:
    global _sheets_manager
    if _sheets_manager is None:
        _sheets_manager = SheetsManager(get_credentials())
    return _sheets_manager

def get_gemini_client():
    """Lazy load the unified Gen AI client"""
    global _genai_client
    if _genai_client is None:
        # The client automatically picks up GOOGLE_CLOUD_PROJECT 
        # and GOOGLE_CLOUD_LOCATION from env vars if vertexai=True
        _genai_client = genai.Client(
            vertexai=True, 
            project=os.environ.get('GCP_PROJECT_ID'),
            location=os.environ.get('GCP_LOCATION', 'us-central1')
        )
    return _genai_client

# ===== DRIVE TOOLS =====

def find_shipment_folder(shipment_number: str) -> dict:
    """
    Finds the Google Drive folder for a shipment by its number.
    Returns {id, name, drive_id} if found, raises exception if not found.
    """
    drive_manager = get_drive_manager()
    result = drive_manager.find_shipment_folder(shipment_number)
    if not result:
        raise Exception(f"Shipment folder not found: {shipment_number}")
    
    # Add drive_id to the result
    year = extract_year_from_shipment(shipment_number)
    drive_id = drive_manager.get_shared_drive_by_year(year)
    result['drive_id'] = drive_id
    
    return result

def list_folder_files(folder_id: str, drive_id: str) -> list[dict]:
    """
    Lists all files in a folder on a shared drive.
    Returns list of {id, name, mimeType}
    """
    return get_drive_manager().list_shipment_files(folder_id, drive_id)

def download_file(file_id: str) -> str:
    """
    Downloads file content from Google Drive and returns as base64 string.
    Use this before sending files to Gemini for analysis.
    """
    content_bytes = get_drive_manager().download_file_content(file_id)
    return base64.b64encode(content_bytes).decode('utf-8')

def move_file_to_folder(file_id: str, folder_id: str) -> dict:
    """
    Moves a file into a specified folder.
    Returns {success: True, file_id, new_parent}
    """
    return get_drive_manager().move_file_to_folder(file_id, folder_id)


# ===== SHEETS TOOLS =====

def create_spreadsheet(title: str, folder_id: str = None) -> dict:
    """
    Creates a new Google Spreadsheet.
    If folder_id provided, moves it to that folder after creation.
    Returns {spreadsheet_id, spreadsheet_url}
    """
    result = get_sheets_manager().create_spreadsheet(title)
    
    if folder_id:
        move_file_to_folder(result['spreadsheet_id'], folder_id)
    
    return result

def append_rows(spreadsheet_id: str, range: str, values: list) -> dict:
    """
    Appends rows to a spreadsheet range.
    values = [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
    Returns API result with updates info.
    """
    return get_sheets_manager().append_rows(spreadsheet_id, range, values)

def get_sheet_values(spreadsheet_id: str, range: str) -> list:
    """
    Reads values from a spreadsheet range.
    Returns list of rows (empty list if range is empty).
    """
    return get_sheets_manager().get_values(spreadsheet_id, range)

def batch_get_sheet_values(spreadsheet_id: str, ranges: list) -> list:
    """
    Reads values from multiple ranges in one call.
    Returns list of ValueRange objects.
    """
    return get_sheets_manager().batch_get_values(spreadsheet_id, ranges)

# ======= GEMINI EXTRACTION TOOLS =======
def extract_invoice_data(file_base64: str, mime_type: str, filename: str) -> dict:
    """
    Extracts invoice data from a file using Gemini Vision.
    
    Args:
        file_base64: Base64-encoded file content
        mime_type: MIME type (e.g., 'application/pdf', 'image/jpeg')
        filename: Original filename for context
    
    Returns:
        {
            "invoice_number": str,
            "date": str,
            "total_amount": float,
            "vendor_name": str,
            "currency": str,
            "issued_to": str,
            "description": str
        }
    """
    __genai_client = get_gemini_client()
    prompt = f"""
        You are extracting structured invoice metadata.

        Return ONLY valid JSON.
        Do not include markdown fences.
        Do not include explanations.

        Schema:
        {{
        "invoice_number": string | null,
        "date": string | null,
        "total_amount": number | null,
        "vendor_name": string | null,
        "currency": string | null,
        "issued_to": string | null,
        "description": string | null
        }}

        Rules:
        - Extract from the document only.
        - If a field is missing or uncertain, return null.
        - date must be exactly as seen unless a clean ISO date is obvious.
        - total_amount must be numeric only, no currency symbols, no commas unless needed for decimal parsing.
        - currency should be the currency code or symbol shown in the invoice.
        - description should be a short summary of what the invoice is for.
        - If the invoice is not in English, translate it to English.
        - If output is not valid JSON, fix it before returning.
        - Use the filename only as weak context: {filename}
    """

    file_bytes = base64.b64decode(file_base64)
    response = __genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)],
        config=types.GenerateContentConfig(
        response_mime_type="application/json"
        )
    )
    return json.loads(response.text)
    
