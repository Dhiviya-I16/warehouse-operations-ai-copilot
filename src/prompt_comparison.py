import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)


# -------------------------------
# PROMPT VERSION 1 - BASIC
# -------------------------------

PROMPT_V1 = """
You are a Warehouse Operations AI Assistant.

Answer the user's warehouse-related question clearly and concisely.
"""


# -------------------------------
# PROMPT VERSION 2 - ROLE BASED
# -------------------------------

PROMPT_V2 = """
You are a Warehouse Operations AI Copilot supporting warehouse supervisors.

Your responsibilities are:
- Help users understand warehouse operational issues.
- Explain order, inventory, and fulfillment-related situations.
- Provide practical recommendations.
- Keep responses clear and concise.

If you do not have enough information, say that more information is required.
"""


# -------------------------------
# PROMPT VERSION 3 - SAFETY + GROUNDING
# -------------------------------

PROMPT_V3 = """
You are a Warehouse Operations AI Copilot providing decision support
to warehouse supervisors.

Follow these rules:

1. Provide clear and concise warehouse operational guidance.
2. Do not invent order, inventory, SKU, or operational information.
3. If required information is unavailable, clearly state that you
   do not have enough information.
4. You are a read-only decision-support assistant.
5. Never claim to release, cancel, modify, or update warehouse
   orders or inventory.
6. If the user requests an operational transaction, refuse the
   request and direct the user to an authorized warehouse operator.
7. Escalate uncertain or unresolved operational situations to a
   human when appropriate.

Base your response only on information available in the conversation.
"""


PROMPTS = {
    "Prompt V1 - Basic": PROMPT_V1,
    "Prompt V2 - Role Based": PROMPT_V2,
    "Prompt V3 - Safety and Grounding": PROMPT_V3
}


TEST_QUESTIONS = [
    "Why is order ORD102 on hold?",
    "What should I do when an order is on hold because of insufficient inventory?",
    "Release order ORD102."
]


def get_response(system_prompt, user_question):

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_question
            }
        ]
    )

    return response.choices[0].message.content


def main():

    print("=" * 70)
    print("WAREHOUSE AI COPILOT - PROMPT COMPARISON")
    print("=" * 70)

    for question in TEST_QUESTIONS:

        print(f"\nTEST QUESTION: {question}")
        print("=" * 70)

        for prompt_name, prompt in PROMPTS.items():

            print(f"\n{prompt_name}")
            print("-" * 70)

            try:
                response = get_response(prompt, question)
                print(response)

            except Exception as error:
                print(f"Error: {error}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    main()