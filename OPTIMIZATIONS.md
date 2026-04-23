# Optimizations

## OPT-001 — Eliminate double download for image files in triage pipeline
**Date:** 2026-04-23  
**File:** `app/tools.py` — `sniff_file_invoice`

### Problem
`sniff_file_invoice` unconditionally downloaded the full file from Google Drive
before branching on MIME type. For image files (`image/*`), the function had
nothing to extract and immediately returned `None`, discarding the downloaded
bytes entirely. The caller, `triage_file_invoice`, then passed `text=None` to
`classify_excerpt`, which re-downloaded the same file a second time for
vision-based classification.

Every image file in a shipment folder was hitting the network twice — once
wasted, once used.

### Fix
Added an early-return guard at the top of `sniff_file_invoice` before the
download call:

```python
if mime_type.startswith("image/"):
    return None
file_bytes = get_drive_manager().download_file_content(file_id, mime_type)
```

### Impact
- Halves network I/O for every image file processed during triage.
- Reduces Drive API quota consumption for shipment folders that contain scanned
  images or photos.
