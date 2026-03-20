TOOL_DEFINITIONS = [
    {
        "name": "find_shipment_folder",
        "description": (
            "Search Google Drive for a shipment folder by shipment number. "
            "Returns the folder ID, Name and the parent drive ID if found."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "shipment_number": {
                    "type": "string",
                    "description": "The shipment number to search for, e.g. 'CLFL26-02-300616'.",
                }
            },
            "required": ["shipment_number"],
        },
    },
    {
        "name": "list_files_in_folder",
        "description": (
            "List all files inside a Google Drive folder. "
            "Returns a list of file objects with id, name, and mimeType."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "folder_id": {
                    "type": "string",
                    "description": "The Google Drive folder ID to list files from.",
                }
            },
            "required": ["folder_id", "drive_id"],
        },
    },
    {
        "name": "download_file",
        "description": (
            "Download a file from Google Drive by its file ID. "
            "Returns the file content as base64 and its MIME type. "
            "Use this before calling extract_invoice_data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The Google Drive file ID to download.",
                },
                "file_name": {
                    "type": "string",
                    "description": "The file name (used for logging and error messages).",
                },
            },
            "required": ["file_id"],
        },
    },
    {
        "name": "move_file",
        "description": "Move a file to a different folder in Google Drive.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The Google Drive file ID to move.",
                },
                "destination_folder_id": {
                    "type": "string",
                    "description": "The folder ID of the destination folder.",
                },
            },
            "required": ["file_id", "destination_folder_id"],
        },
    },
    {
        "name": "extract_invoice_data",
        "description": (
            "Extract structured invoice data from a file using Gemini Vision. "
            "Accepts PDFs and images (scanned or digital). "
            "Returns fields: invoice_number, date, vendor_name, issued_to, "
            "description, total_amount, currency."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_base64": {
                    "type": "string",
                    "description": "Base64-encoded file content returned by download_file.",
                },
                "mime_type": {
                    "type": "string",
                    "description": "MIME type of the file, e.g. 'application/pdf' or 'image/jpeg'.",
                },
                "filename": {
                    "type": "string",
                    "description": "Original file name, used for logging.",
                },
            },
            "required": ["file_base64", "mime_type", "filename"],
        },
    },
    {
        "name": "create_spreadsheet",
        "description": (
            "Create a new Google Sheet inside a specified Drive folder. "
            "Returns the spreadsheet ID and URL."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the new spreadsheet, e.g. 'CLFL26-02-300616 Invoices'.",
                },
                "folder_id": {
                    "type": "string",
                    "description": "Google Drive folder ID where the sheet will be created.",
                },
            },
            "required": ["title", "folder_id"],
        },
    },
    {
        "name": "append_rows",
        "description": (
            "Append one or more rows of data to a Google Sheet. "
            "Call once with all invoice rows after extraction is complete — "
            "do not call once per invoice."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Sheets spreadsheet ID.",
                },
                "rows": {
                    "type": "array",
                    "description": (
                        "List of rows to append. Each row is a list of cell values "
                        "in this order: invoice_number, date, vendor_name, issued_to, "
                        "description, total_amount, currency."
                    ),
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            "required": ["spreadsheet_id", "rows"],
        },
    },
    {
        "name": "get_sheet_values",
        "description": "Read a range of values from a Google Sheet. Useful for verification.",
        "parameters": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Sheets spreadsheet ID.",
                },
                "range": {
                    "type": "string",
                    "description": "A1 notation range, e.g. 'Sheet1!A1:G50'.",
                },
            },
            "required": ["spreadsheet_id", "range"],
        },
    },
]