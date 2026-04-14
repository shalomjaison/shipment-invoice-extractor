from google import genai
from google.genai import types
import os
from app.tools_definitions import TOOL_DEFINITIONS
from app.tools import find_shipment_folder, list_folder_files, move_file_to_folder, create_spreadsheet, append_rows, get_sheet_values, batch_get_sheet_values, extract_invoice_data
from dotenv import load_dotenv
from google.oauth2 import service_account
load_dotenv()

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'shipment-invoice-extractor')
LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')


credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=credentials)

tool_map = {
    "find_shipment_folder": find_shipment_folder,
    "list_folder_files": list_folder_files,
    "move_file_to_folder": move_file_to_folder,
    "create_spreadsheet": create_spreadsheet,
    "append_rows": append_rows,
    "get_sheet_values": get_sheet_values,
    "batch_get_sheet_values": batch_get_sheet_values,
    "extract_invoice_data": extract_invoice_data
}

tools = [
    types.Tool(function_declarations=[types.FunctionDeclaration(**t) for t in TOOL_DEFINITIONS])
]


if __name__ == '__main__':
    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(tools=tools)
        )

        response = chat.send_message("CLFL25-11-203994 Create a spreadsheet with all debit notes for this shipment")
        while True:
            agent_response = {}
            parts = []
            if response.function_calls:
                print(f"Model wants to call {len(response.function_calls)} tool(s):")
                for fc in response.function_calls:
                    print(f"  tool: {fc.name}")
                    print(f"  args: {dict(fc.args)}")
                    if fc.name in tool_map:
                        agent_response[fc.name] = tool_map[fc.name](**dict(fc.args))
                        parts.append(types.Part(function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": agent_response[fc.name]}
                        )))
                        print(f"Tool {fc.name} called with args {dict(fc.args)} and result {agent_response[fc.name]}")
                    else:
                        agent_response[fc.name] = "Tool not found"
            else:
                print(response.text)
                break
            response = chat.send_message(parts)
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()
