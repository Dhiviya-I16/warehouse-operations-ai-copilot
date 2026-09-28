import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
# 2. LOAD WAREHOUSE SOP
# --------------------------------------------------

project_root = Path(__file__).resolve().parent.parent
sop_path = project_root / "data" / "warehouse_sop.txt"

with open(sop_path, "r", encoding="utf-8") as file:
    sop_text = file.read()


# --------------------------------------------------
# 3. SPLIT SOP INTO CHUNKS
# --------------------------------------------------

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100
)

chunks = text_splitter.create_documents([sop_text])


# --------------------------------------------------
# 4. CREATE EMBEDDINGS AND VECTOR STORE
# --------------------------------------------------

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
# 5. SYSTEM PROMPT - OUR SELECTED PROMPT V3
# --------------------------------------------------

SYSTEM_PROMPT = """
You are a Warehouse Operations AI Copilot providing decision support
to warehouse supervisors.

Follow these rules:

1. Answer using the warehouse SOP context provided to you.
2. Do not invent order, inventory, SKU, or operational information.
3. If the retrieved context does not contain enough information,
   clearly state that the information is unavailable.
4. You are a read-only decision-support assistant.
5. Never claim to release, cancel, modify, or update warehouse
   orders or inventory.
6. If the user requests an operational transaction, refuse the
   request and direct the user to an authorized warehouse operator.
7. Escalate uncertain or unresolved situations to a human when appropriate.
8. Keep the response clear and concise.
"""


# --------------------------------------------------
# 6. RETRIEVE RELEVANT SOP INFORMATION
# --------------------------------------------------

def retrieve_context(user_query):
    documents = vector_store.similarity_search(
        user_query,
        k=2
    )

    context = "\n\n".join(
        document.page_content for document in documents
    )

    return context


# --------------------------------------------------
# 7. GENERATE RAG RESPONSE
# --------------------------------------------------

def get_rag_response(user_query):

    context = retrieve_context(user_query)

    user_message = f"""
WAREHOUSE SOP CONTEXT:

{context}

USER QUESTION:

{user_query}
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return response.choices[0].message.content, context


# --------------------------------------------------
# 8. MAIN APPLICATION
# --------------------------------------------------

def main():

    print("=" * 60)
    print("Warehouse Operations AI Copilot - RAG Agent")
    print("=" * 60)
    print("Type 'exit' to close the application.\n")

    while True:

        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        try:

            response, context = get_rag_response(user_query)

            print("\n--- Retrieved SOP Context ---")
            print(context)

            print("\n--- Agent Response ---")
            print(response)

            print("\n" + "-" * 60)

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()