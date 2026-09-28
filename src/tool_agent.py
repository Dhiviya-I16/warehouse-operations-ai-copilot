import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from warehouse_tools import get_order_status, check_inventory


# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)


# --------------------------------------------------
# 2. DEFINE TOOLS FOR THE LLM
# --------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Retrieve read-only warehouse order information using an order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Warehouse order ID, for example ORD102."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Retrieve the available inventory quantity for a warehouse SKU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Warehouse SKU, for example SKU204."
                    }
                },
                "required": ["sku"]
            }
        }
    }
]


# --------------------------------------------------
# 3. SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are a Warehouse Operations AI Copilot providing read-only
decision support to warehouse supervisors.

Rules:

1. Use the available tools when operational order or inventory
   information is required.
2. Never invent order status, SKU information, or inventory quantities.
3. If a tool cannot find the requested information, clearly state
   that the information is unavailable.
4. Never release, cancel, modify, or update warehouse orders or inventory.
5. If the user requests an operational transaction, refuse the request
   and direct them to an authorized warehouse operator.
6. Keep responses clear and concise.
"""


# --------------------------------------------------
# 4. EXECUTE AN APPROVED TOOL
# --------------------------------------------------

def execute_tool(tool_name, arguments):
    """
    Execute only tools explicitly approved by this application.
    """

    if tool_name == "get_order_status":
        return get_order_status(arguments["order_id"])

    if tool_name == "check_inventory":
        return check_inventory(arguments["sku"])

    return {
        "success": False,
        "error": f"Tool '{tool_name}' is not allowed."
    }


# --------------------------------------------------
# 5. PROCESS USER QUESTION
# --------------------------------------------------

def process_query(user_query):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    # Ask the LLM whether a tool is required
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message

    # If no tool is required, return the normal LLM response
    if not assistant_message.tool_calls:
        return assistant_message.content, []

    messages.append(assistant_message)

    tool_history = []

    # Limit tool execution to prevent uncontrolled repeated calls
    max_tool_calls = 3

    for tool_call in assistant_message.tool_calls[:max_tool_calls]:

        tool_name = tool_call.function.name

        try:
            arguments = json.loads(tool_call.function.arguments)
            tool_result = execute_tool(tool_name, arguments)

        except Exception as error:
            tool_result = {
                "success": False,
                "error": str(error)
            }

        tool_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "result": tool_result
        })

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })

    # Give tool results back to the LLM
    final_response = client.chat.completions.create(
        model=model_name,
        messages=messages
    )

    return final_response.choices[0].message.content, tool_history


# --------------------------------------------------
# 6. MAIN APPLICATION
# --------------------------------------------------

def main():

    print("=" * 60)
    print("Warehouse Operations AI Copilot - Tool Agent")
    print("=" * 60)
    print("Type 'exit' to close the application.\n")

    while True:

        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        try:

            response, tool_history = process_query(user_query)

            if tool_history:
                print("\n--- Tool Usage ---")

                for item in tool_history:
                    print(f"Tool: {item['tool']}")
                    print(f"Arguments: {item['arguments']}")
                    print(f"Result: {item['result']}")

            else:
                print("\n--- Tool Usage ---")
                print("No tool used.")

            print("\n--- Agent Response ---")
            print(response)

            print("\n" + "-" * 60)

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()