from google.oauth2 import service_account
import os
from google import genai
import google.auth

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

_credentials = None
_genai_client = None
def initialize_credentials():
    global _credentials
    use_user_credentials = os.environ.get("USE_USER_CREDENTIALS", "").lower() in {"1", "true", "yes"}
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or GOOGLE_APPLICATION_CREDENTIALS
    if _credentials is None:
        if use_user_credentials:
            _credentials, _ = google.auth.default(scopes=SCOPES)
        else:
            if not creds_path:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
            _credentials = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return _credentials

def get_credentials():
    if _credentials is None:
        initialize_credentials()
    return _credentials


def get_gemini_client():
    """Lazy load the unified Gen AI client"""
    global _genai_client
    if _genai_client is None:
        project_id = (
            os.environ.get('GOOGLE_CLOUD_PROJECT')
            or os.environ.get('GCP_PROJECT_ID')
        )
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set")
        location = (
            os.environ.get('GOOGLE_CLOUD_LOCATION')
            or os.environ.get('GCP_LOCATION')
            or 'us-central1'
        )
        _genai_client = genai.Client(
            vertexai=True, 
            project=project_id,
            location=location
        )
    return _genai_client

