import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from warehouse_tools import get_order_status, check_inventory


# --------------------------------------------------
# 1. ENVIRONMENT SETUP
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
# 2. LOAD SOP AND CREATE RAG KNOWLEDGE BASE
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOP_PATH = PROJECT_ROOT / "data" / "warehouse_sop.txt"

with open(SOP_PATH, "r", encoding="utf-8") as file:
    sop_text = file.read()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100
)

chunks = text_splitter.create_documents([sop_text])

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key,
    base_url=base_url
)

vector_store = FAISS.from_documents(
    chunks,
    embedding_model
)


# --------------------------------------------------
# 3. TOOL DEFINITIONS
# --------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Retrieve read-only operational information for "
                "a warehouse order using an order ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID, for example ORD102."
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
            "description": (
                 "Retrieve available warehouse inventory for a SKU. "
                 "Use only a SKU identifier beginning with 'SKU'. "
                 "Never pass an order ID such as ORD102 to this tool. "
                 "If investigating an order, first use get_order_status "
                 "and use the SKU returned by that tool."
                 ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Warehouse SKU beginning with SKU, for example SKU204. "
                        "Do not provide an order ID."
                    }
                },
                "required": ["sku"]
            }
        }
    }
]


# --------------------------------------------------
# 4. FINAL SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are a Warehouse Operations AI Copilot providing read-only
decision support to warehouse supervisors.

You have access to:
- Read-only order information
- Read-only inventory information
- Retrieved Warehouse SOP context
- Current-session conversation history

Follow these rules:

1. Use available tools when current order or inventory data is required.
2. Use the provided SOP context for warehouse procedural guidance.
3. Use relevant earlier conversation information for follow-up questions.
4. You may perform multiple read-only tool calls when an investigation
   requires more than one step.
5. Never invent order status, SKU data, inventory quantities, or SOP rules.
6. If information is unavailable or cannot be verified, clearly say so.
7. Never release, cancel, modify, or update orders or inventory.
8. Refuse transactional requests and direct the user to an authorized
   warehouse operator.
9. Escalate when the SOP does not provide sufficient guidance or when
   the safe next step is uncertain.
10. Keep responses concise and explain the basis for the recommendation.
"""


# --------------------------------------------------
# 5. RETRIEVE SOP CONTEXT
# --------------------------------------------------

def retrieve_context(user_query):

    documents = vector_store.similarity_search(
        user_query,
        k=2
    )

    return "\n\n".join(
        document.page_content for document in documents
    )


# --------------------------------------------------
# 6. EXECUTE ONLY APPROVED READ-ONLY TOOLS
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
# 7. PROCESS QUERY
# --------------------------------------------------

def process_query(user_query, conversation_history):

    # Retrieve SOP information relevant to this question
    sop_context = retrieve_context(user_query)

    user_message = f"""
USER QUESTION:
{user_query}

RETRIEVED WAREHOUSE SOP CONTEXT:
{sop_context}
"""

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    tool_history = []

    # Prevent uncontrolled tool loops
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

        # No tool requested -> final answer
        if not assistant_message.tool_calls:

            final_answer = assistant_message.content

            conversation_history.append({
                "role": "assistant",
                "content": final_answer
            })

            return final_answer, tool_history, sop_context

        conversation_history.append(assistant_message)

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

                tool_result = execute_tool(
                    tool_name,
                    arguments
                )

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
        "I could not safely complete this request within the "
        "allowed investigation steps. Please escalate to an "
        "authorized warehouse operator.",
        tool_history,
        sop_context
    )


# --------------------------------------------------
# 8. MAIN APPLICATION
# --------------------------------------------------

def main():

    print("=" * 68)
    print("Warehouse Operations AI Copilot - Final Integrated Agent")
    print("=" * 68)

    print(
        "Read-only decision support using RAG, tools, "
        "memory and safety controls."
    )

    print("Type 'exit' to close the application.\n")

    conversation_history = []

    while True:

        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        try:

            response, tool_history, sop_context = process_query(
                user_query,
                conversation_history
            )

            print("\n--- Retrieved SOP Context ---")
            print(sop_context)

            print("\n--- Tool / Planning Trace ---")

            if tool_history:

                for item in tool_history:
                    print(f"Tool: {item['tool']}")
                    print(f"Arguments: {item['arguments']}")
                    print(f"Result: {item['result']}")

            else:
                print("No operational tool used.")

            print("\n--- Agent Response ---")
            print(response)

            print("\n" + "-" * 68)

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()