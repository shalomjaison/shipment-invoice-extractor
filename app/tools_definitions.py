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
            "The file is downloaded internally using the file_id."
            "Accepts PDFs and images (scanned or digital). "
            "Returns fields: invoice_number, date, vendor_name, issued_to, "
            "description, total_amount, currency."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The Google Drive file ID to extract data from.",
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
            "required": ["file_id", "mime_type", "filename"],
        },
    },
    {
        "name": "sniff_file_invoice",
        "description": (
            "Download a file from Google Drive and extract a short text sample for triage. "
            "Used as a cheap first pass before sending a document to an LLM classifier. "
            "Returns up to 500 characters of extracted text, or null if the file requires "
            "vision-based classification (e.g. images)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID to download."
                },
                "mime_type": {
                    "type": "string",
                    "description": (
                        "MIME type of the file. Supported: application/pdf, "
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document, "
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, "
                        "message/rfc822, image/*. Unsupported types return null."
                    )
                }
            },
            "required": ["file_id", "mime_type"]
        }
    },
    {
        "name": "classify_excerpt",
        "description": (
            "Classify a document as 'relevant' or 'skip' using Gemini Flash Lite. "
            "Operates in two modes: text mode (when a text excerpt is provided) or vision mode "
            "(when text is null, downloads and sends raw image bytes to the model). "
            "Returns exactly one of: 'relevant' or 'skip'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID. Only downloaded in vision mode (when text is null)."
                },
                "mime_type": {
                    "type": "string",
                    "description": "MIME type of the file. Used for the inline Part in vision mode."
                },
                "text": {
                    "type": ["string", "null"],
                    "description": (
                        "Short text excerpt from sniff_file_invoice. "
                        "Pass null to trigger vision mode for image-only documents."
                    )
                },
                "user_prompt": {
                    "type": "string",
                    "description": "The original user request describing what files to look for."
                }
            },
            "required": ["file_id", "mime_type", "text", "user_prompt"]
        }
    },
    {
        "name": "triage_file_invoice",
        "description": (
            "Decide whether a file should be extracted, skipped, or recursed into. "
            "Entry point for the pre-extraction triage stage. Runs a layered pipeline: "
            "(1) hard MIME skip for archives/video/audio, "
            "(2) folder check returning 'recurse', "
            "(3) text sniff via sniff_file_invoice, "
            "(4) LLM classification via classify_excerpt. "
            "Returns 'relevant' (pass to extract_invoice_data), "
            "'skip' (ignore), or 'recurse' (list folder contents and triage children)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID."
                },
                "mime_type": {
                    "type": "string",
                    "description": "MIME type used to route through the triage pipeline."
                },
                "user_prompt": {
                    "type": "string",
                    "description": "The original user request, forwarded to the LLM classifier."
                }
            },
            "required": ["file_id", "mime_type", "user_prompt"]
        }
    },
    {
        "name": "triage_folder_files",
        "description": "Runs triage on a list of files from a shipment folder to determine which are relevant for invoice extraction. Returns a dict of file_id to classification (relevant, skip, or recurse).",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of file objects with id and mimetype",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "mimeType": {"type": "string"}
                        },
                        "required": ["id", "mimeType"]
                    }
                },
                "user_prompt": {
                    "type": "string",
                    "description": "The original user request describing what kind of files to look for."
                }
            },
            "required": ["files", "user_prompt"],
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
    {
        "name": "batch_get_sheet_values",
        "description": "Read multiple ranges of values from a Google Sheet. Useful for verification.",
        "parameters": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Sheets spreadsheet ID.",
                },
                "ranges": {
                    "type": "array",
                    "description": "The ranges of the spreadsheet to read from, e.g. ['Sheet1!A1:G50', 'Sheet1!H1:M50'].",
                }
            },
            "required": ["spreadsheet_id", "ranges"],
        },
    }
]