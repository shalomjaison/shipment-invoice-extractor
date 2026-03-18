from google import genai
from google.auth import default
import os
from dotenv import load_dotenv
from google.genai.types import Part, Blob
import base64

load_dotenv()

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'shipment-invoice-extractor')
LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

prompt = """
You are a highly skilled document summarization specialist. Your task is to provide a concise summary of
no more than 300 words of the following document. Please summarize the document for a general audience.
"""

with open("./Invoice-Validation-Before-SABER.pdf", "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode('utf-8')

pdf_part = Part(inline_data=Blob(mime_type="application/pdf", data=pdf_data))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[pdf_part, prompt]
)
print(response.text)