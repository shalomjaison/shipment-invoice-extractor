# Shipment Invoice Extractor

A FastAPI service that classifies and extracts data from shipment invoices using **Vertex AI Gemini**. Results are written to Google Sheets via the Sheets/Drive APIs.

## Architecture

```
Client
  └─ POST /classify  (base64-encoded document + mime type)
       └─ Vertex AI Gemini  (classification & extraction)
            └─ Google Sheets  (output)
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/test-auth` | Verify service account credentials |
| `POST` | `/classify` | Classify and extract a document |

### `POST /classify` request body

```json
{
  "filename": "invoice.pdf",
  "mime_type": "application/pdf",
  "base64_content": "<base64-encoded file>"
}
```

## Setup

### Prerequisites
- Python 3.11+
- A GCP project with Vertex AI, Sheets, and Drive APIs enabled
- A service account with appropriate roles, and its JSON key file

### Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON key | `secrets/shipment-invoice-extractor-1300acac7dd8.json` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `shipment-invoice-extractor` |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region | `us-central1` |

### Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Run with Docker

```bash
docker build -t shipment-invoice-extractor .
docker run -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/your-key.json \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -v $(pwd)/secrets:/app/secrets \
  shipment-invoice-extractor
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` / `uvicorn` | Web framework |
| `google-cloud-aiplatform` | Vertex AI Gemini SDK |
| `google-cloud-storage` | GCS document storage |
| `gspread` | Google Sheets write-back |
| `google-auth` / `google-auth-oauthlib` | GCP authentication |
| `pydantic` | Request validation |
