from clfl_core_library import DriveManager, extract_year_from_shipment, SheetsManager
from google.genai import types
from google.oauth2 import service_account
import google.auth
from google import genai
import base64
import os
import json

_drive_manager = None
_sheets_manager = None
_genai_client = None
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CREDS = os.path.join(
    PROJECT_ROOT,
    "secrets",
    "shipment-invoice-extractor-1300acac7dd8.json",
)

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS",
    DEFAULT_CREDS,
)

def get_credentials():
    """Shared credentials loader"""
    if os.environ.get('USE_USER_CREDENTIALS') == '1':
        creds, _ = google.auth.default(scopes=SCOPES)
        print(f"[DEBUG] Using ADC credentials: type={type(creds).__name__}")
        return creds
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or GOOGLE_APPLICATION_CREDENTIALS
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    print(f"[DEBUG] Using service account: {creds.service_account_email}")
    return creds

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

# def download_file(file_id: str) -> str:
#     """
#     Downloads file content from Google Drive and returns as base64 string.
#     Use this before sending files to Gemini for analysis.
#     """
#     content_bytes = get_drive_manager().download_file_content(file_id)
#     return base64.b64encode(content_bytes).decode('utf-8')

def move_file_to_folder(file_id: str, folder_id: str) -> dict:
    """
    Moves a file into a specified folder.
    Returns {success: True, file_id, new_parent}
    """
    return get_drive_manager().move_file_to_folder(file_id, folder_id)


# ===== SHEETS TOOLS =====

def create_spreadsheet(title: str, folder_id: str = None) -> dict:
    """
    Creates a new Google Spreadsheet via Drive API (bypasses Sheets API permission restriction).
    If folder_id provided, places it directly in that folder.
    Returns {spreadsheet_id, spreadsheet_url}
    """
    
    return get_drive_manager().create_spreadsheet(title, folder_id)

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
def extract_invoice_data(mime_type: str, filename: str, file_id: str) -> dict:
    """
    Extracts invoice data from a file using Gemini Vision. Accepts a file ID and downloads the file content internally.
    
    Args:
        mime_type: MIME type (e.g., 'application/pdf', 'image/jpeg')
        filename: Original filename for context
        file_id: Google Drive file ID
    
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

    file_bytes = get_drive_manager().download_file_content(file_id, mime_type)
    print(f"[DEBUG] Downloaded {len(file_bytes)} bytes for file_id={file_id}, mime_type={mime_type}")
    if not file_bytes:
        raise ValueError(f"Downloaded file is empty: {file_id}")
    response = __genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)],
        config=types.GenerateContentConfig(
        response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

def sniff_file_invoice(file_id: str, mime_type: str) -> str:
    """
    Download a file and extract a quick text sample for invoice triage.

    Supports PDF (first page text) and DOCX (first paragraph text).
    Raises ValueError if the downloaded file is empty.
    Returns the extracted text snippet used for relevance checks.
    """
    file_bytes = get_drive_manager().download_file_content(file_id, mime_type)
    if not file_bytes:
        raise ValueError(f"Downloaded file is empty: {file_id}")
    
    import io
    if mime_type == "application/pdf":
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if text is None:
                return None
            print(f"[DEBUG] Sniffed text: {text}")
    
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        text = doc.paragraphs[0].text
        print(f"[DEBUG] Sniffed text: {text}")
    
    elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        import openpyxl
        workbook = openpyxl.load_workbook(io.BytesIO(file_bytes))
        sheet = workbook.active
        extracted_data = []
        for row in sheet.iter_rows(max_row=10, values_only=True):
            row_text = " | ".join(str(cell) for cell in row if cell is not None)
            if row_text: extracted_data.append(row_text)
        workbook.close()
        text = "\n".join(extracted_data)
    
    elif mime_type.startswith("image/"):
        return None
    
    elif mime_type == "message/rfc822":
        import email
        msg = email.message_from_bytes(file_bytes)
        text = msg.get_payload(decode=True)
        if text is None:
            return None
        text = text.decode('utf-8')

    
    return text[:500]

def classify_excerpt(file_id: str, mime_type: str, text: str | None, user_prompt: str) -> str:
    __genai_client = get_gemini_client()
    if text is not None:
        prompt = f"""
        You are a document classifier for a freight forwarding company with 15 years of experience handling shipment files.

        You will be given a user prompt and a short excerpt from a document. Your job is to determine whether the document is relevant to the user's request.

        User prompt:
        ```{user_prompt}```

        Document excerpt:
        ```{text}```

        Reply with ONLY one word — either "relevant" or "skip". No explanation. No punctuation. No other text.
        """
        response = __genai_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[prompt],
            config=types.GenerateContentConfig(response_mime_type="text/plain")
        )
    else:
        file_bytes = get_drive_manager().download_file_content(file_id, mime_type)
        if not file_bytes:
            raise ValueError(f"Downloaded file is empty: {file_id}")
        
        prompt = f"""
        You are a document classifier for a freight forwarding company with 15 years of experience handling shipment files.
        You will be given an image of a document or a scanned document. Your job is to determine whether the document is relevant to the user's request.

        User prompt:
        ```{user_prompt}```

        Reply with ONLY one word — either "relevant" or "skip". No explanation. No punctuation. No other text.
        """
        response = __genai_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)],
            config=types.GenerateContentConfig(response_mime_type="text/plain")
        )
    
    return response.text.strip().lower()



def triage_file_invoice(file_id: str, file_name: str, mime_type: str, user_prompt: str) -> str:
    """
    Determine whether a file should be processed for invoice extraction.

    Inputs: `file_id`, `file_name`, and `mime_type`.
    Returns one of: `relevant`, `skip`, or `recurse`.

    Decision flow for this function:
    list_folder_files -> triage (hard MIME skip -> text sniff -> keyword scan -> Flash classify) -> full extraction.
    Called by the orchestrator before `extract_invoice_data` (full extraction).
    """
    # Layer 1: Hard MIME SKIP for INVOICE FILES AS OF NOW
    HARD_SKIP_MIME_TYPES = [
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "video/mp4",
        "video/quicktime",
        "audio/mpeg",
        "audio/wav",
    ]

    if mime_type in HARD_SKIP_MIME_TYPES:
        return "skip"
    elif mime_type == "application/vnd.google-apps.folder":
        return "recurse"
    
    text = sniff_file_invoice(file_id, mime_type)
    return classify_excerpt(file_id, mime_type, text, user_prompt)
