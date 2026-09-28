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
# 2. DEFINE AVAILABLE TOOLS
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
            "description": "Retrieve available inventory quantity for a warehouse SKU.",
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

1. Use the available tools when order or inventory information is required.
2. Use relevant information from earlier messages when the user asks
   follow-up questions.
3. For an order investigation, you may use multiple read-only tools
   when needed to understand the issue.
4. Never invent order status, SKU information, or inventory quantities.
5. If information cannot be found, clearly state that it is unavailable.
6. Never release, cancel, modify, or update warehouse orders or inventory.
7. Refuse requests for operational transactions and direct the user
   to an authorized warehouse operator.
8. Keep responses clear and concise.
"""


# --------------------------------------------------
# 4. EXECUTE APPROVED TOOLS
# --------------------------------------------------

def execute_tool(tool_name, arguments):

    if tool_name == "get_order_status":
        return get_order_status(arguments["order_id"])

    if tool_name == "check_inventory":
        return check_inventory(arguments["sku"])

    return {
        "success": False,
        "error": f"Tool '{tool_name}' is not allowed."
    }


# --------------------------------------------------
# 5. PROCESS QUERY WITH MEMORY AND MULTI-STEP TOOL USE
# --------------------------------------------------

def process_query(user_query, conversation_history):

    conversation_history.append({
        "role": "user",
        "content": user_query
    })

    tool_history = []
    max_rounds = 3

    for _ in range(max_rounds):

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + conversation_history,
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # No more tool calls means the agent has reached its final answer
        if not assistant_message.tool_calls:

            final_answer = assistant_message.content

            conversation_history.append({
                "role": "assistant",
                "content": final_answer
            })

            return final_answer, tool_history

        conversation_history.append(assistant_message)

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
                tool_result = execute_tool(tool_name, arguments)

            except Exception as error:
                arguments = {}
                tool_result = {
                    "success": False,
                    "error": str(error)
                }

            tool_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": tool_result
            })

            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

    return (
        "I could not complete the investigation within the allowed tool-call rounds. "
        "Please escalate to a warehouse operator.",
        tool_history
    )


# --------------------------------------------------
# 6. MAIN APPLICATION
# --------------------------------------------------

def main():

    print("=" * 65)
    print("Warehouse Operations AI Copilot - Memory & Planning Agent")
    print("=" * 65)
    print("Type 'exit' to close the application.\n")

    # This list stores the current conversation
    conversation_history = []

    while True:

        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        try:

            response, tool_history = process_query(
                user_query,
                conversation_history
            )

            if tool_history:
                print("\n--- Tool / Planning Trace ---")

                for item in tool_history:
                    print(f"Tool: {item['tool']}")
                    print(f"Arguments: {item['arguments']}")
                    print(f"Result: {item['result']}")

            else:
                print("\n--- Tool / Planning Trace ---")
                print("No new tool used.")

            print("\n--- Agent Response ---")
            print(response)

            print("\n" + "-" * 65)

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()