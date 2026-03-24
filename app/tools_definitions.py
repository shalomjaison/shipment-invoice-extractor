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
        "name": "list_folder_files",
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
                },
                "drive_id": {
                    "type": "string",
                    "description": "The Google Drive ID that the folder from which the files are listed belongs to.",
                },
            },
            "required": ["folder_id", "drive_id"],
        },
    },
    {
        "name": "download_file",
        "description": (
            "Download a file from Google Drive by its file ID. "
            "Returns the file content as base64. "
            "Use this before calling extract_invoice_data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The Google Drive file ID to download.",
                },
            },
            "required": ["file_id"],
        },
    },
    {
        "name": "move_file_to_folder",
        "description": "Move a file to a different folder in Google Drive. ",
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The Google Drive file ID to move.",
                },
                "folder_id": {
                    "type": "string",
                    "description": "The Google Drive folder ID to move the file to.",
                },
            },
            "required": ["file_id", "folder_id"],
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
                "range": {
                    "type": "string",
                    "description": "The range of the spreadsheet to append the rows to, e.g. 'Sheet1!A1:G50'.",
                },
                "values": {
                    "type": "array",
                    "description": "List of rows to append. Each row is a list of cell values.",
                },
            },
            "required": ["spreadsheet_id", "range", "values"],
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