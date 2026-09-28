import os
from dotenv import load_dotenv
from openai import OpenAI

# Load values stored in the .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Create the LLM client
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)


def get_llm_response(user_query):
    """
    Send the user's question to the LLM and return its response.
    """

    system_prompt = """
    You are a Warehouse Operations AI Assistant.

    Your role is to help warehouse supervisors understand
    operational issues and provide useful guidance.

    Answer the user's question clearly and concisely.
    """

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    return response.choices[0].message.content


def main():
    print("=" * 55)
    print("Warehouse Operations AI Copilot - LLM Agent")
    print("=" * 55)
    print("Type 'exit' to close the application.\n")

    while True:

        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        try:
            response = get_llm_response(user_query)

            print(f"\nAgent: {response}\n")

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()