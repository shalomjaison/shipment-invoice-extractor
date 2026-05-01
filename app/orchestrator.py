from google.genai import types
from app.tools_definitions import TOOL_DEFINITIONS
from app.tools import find_shipment_folder, list_folder_files, move_file_to_folder, create_spreadsheet, append_rows, get_sheet_values, batch_get_sheet_values, extract_invoice_data, triage_folder_files, sniff_file_invoice, classify_excerpt, triage_file_invoice
from dotenv import load_dotenv
from app.utils import get_gemini_client

load_dotenv()

tool_map = {
    "find_shipment_folder": find_shipment_folder,
    "list_folder_files": list_folder_files,
    "move_file_to_folder": move_file_to_folder,
    "create_spreadsheet": create_spreadsheet,
    "append_rows": append_rows,
    "get_sheet_values": get_sheet_values,
    "batch_get_sheet_values": batch_get_sheet_values,
    "extract_invoice_data": extract_invoice_data,
    "sniff_file_invoice": sniff_file_invoice,
    "classify_excerpt": classify_excerpt,
    "triage_file_invoice": triage_file_invoice,
    "triage_folder_files": triage_folder_files
}

tools = [
    types.Tool(function_declarations=[types.FunctionDeclaration(**t) for t in TOOL_DEFINITIONS])
]


def run_agent(user_message: str):
    try:
        client = get_gemini_client()
        chat = client.chats.create(model="gemini-2.5-flash", config=types.GenerateContentConfig(tools=tools))

        response = chat.send_message(user_message)
        function_calls_counter = 0
        while function_calls_counter < 25:
            function_calls_counter += 1
            agent_response = {}
            parts = []
            if response.function_calls:
                print(f"Model wants to call {len(response.function_calls)} tool(s):")
                for fc in response.function_calls:
                    print(f"  tool: {fc.name}")
                    print(f"  args: {dict(fc.args)}")
                    if fc.name in tool_map:
                        try:
                            agent_response[fc.name] = tool_map[fc.name](**dict(fc.args))
                            parts.append(types.Part(function_response=types.FunctionResponse(
                                name=fc.name,
                                response={"result": agent_response[fc.name]}
                            )))
                        except Exception as e:
                            agent_response[fc.name] = f"{type(e).__name__}: {e}"
                            parts.append(types.Part(function_response=types.FunctionResponse(
                                name=fc.name,
                                response={"error": agent_response[fc.name]}
                            )))
                            print(f"Error: {type(e).__name__}: {e}")
                        print(f"Tool {fc.name} called with args {dict(fc.args)} and result {agent_response[fc.name]}")
                    else:
                        print(f"Tool {fc.name} not found")
                        agent_response[fc.name] = "Tool not found"
                        parts.append(types.Part(function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"error": f"Tool '{fc.name}' is not available"}
                        )))
            else:
                return response.text
            
            response = chat.send_message(parts)
        
        if function_calls_counter >= 25:
            return "Maximum number of function calls reached. Please try again with a more specific request."
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise e



if __name__ == "__main__":
    user_message = "CLFL25-11-203994 Create a spreadsheet with all debit notes for this shipment"
    print(run_agent(user_message))
