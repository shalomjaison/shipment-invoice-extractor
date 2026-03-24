import sys, os
from dotenv import load_dotenv

load_dotenv()

from app.tools import find_shipment_folder, list_folder_files, download_file, extract_invoice_data

def test_shipment(shipment_number: str):
    print(f"\n{'='*60}")
    print(f"Testing Shipment: {shipment_number}")
    print(f"{'='*60}\n")

    print("1. Finding shipment folder...")
    try:
        shipment_folder = find_shipment_folder(shipment_number)
        print(f"   ✓ Found: {shipment_folder['name']}")
        print(f"   ✓ Folder ID: {shipment_folder['id']}")
        print(f"   ✓ Drive ID: {shipment_folder['drive_id']}")
    except Exception as e:
        print(f"   ✗ Error finding shipment folder: {e}")
        return

    print("\n2. Listing files in folder...")
    try:
        shipment_files = list_folder_files(shipment_folder['id'], shipment_folder['drive_id'])
        print(f"   ✓ Found {len(shipment_files)} files")
        for file in shipment_files:
            print(f"   ✓ File: {file['name']}")
            print(f"   ✓ File ID: {file['id']}")
            print(f"   ✓ File MIME Type: {file['mimeType']}")
    except Exception as e:
        print(f"   ✗ Error listing files: {e}")
        return
    
    if not shipment_files:
        print("   ✗ No files found in shipment folder")
        return
    
    print("\n3. Testing download & extraction on first file...")
    first_file = shipment_files[0]
    try:
        print(f"   Downloading: {first_file['name']}...")
        file_base64 = download_file(first_file['id'])
        print(f"   ✓ Downloaded {len(file_base64)} base64 chars")

        mime_type = first_file['mimeType']
        if mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']:
            print(f"   Extracting invoice data...")
            invoice_data = extract_invoice_data(
                file_base64, 
                mime_type, 
                first_file['name']
            )
            print(f"   ✓ Extraction complete:")
            print(f"      Invoice #: {invoice_data.get('invoice_number')}")
            print(f"      Date: {invoice_data.get('date')}")
            print(f"      Amount: {invoice_data.get('total_amount')} {invoice_data.get('currency')}")
            print(f"      Vendor: {invoice_data.get('vendor_name')}")
            print(f"      Issued To: {invoice_data.get('issued_to')}")
            print(f"      Description: {invoice_data.get('description')}")
        else:
            print(f"   ⊘ Skipping extraction (not PDF/image): {mime_type}")
    
    except Exception as e:
        print(f"   ✗ Error extracting invoice data: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Test complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_shipment.py <shipment_number>")
        print("Example: python test_shipment.py 24-1234")
        sys.exit(1)
    
    shipment_number = sys.argv[1]
    test_shipment(shipment_number)
