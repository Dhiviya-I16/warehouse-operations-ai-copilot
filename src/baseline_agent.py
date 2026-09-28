from datetime import datetime


def get_baseline_response(user_query):
    """
    Generate a simple rule-based response.
    This baseline does not use an LLM, RAG, tools, or memory.
    """

    query = user_query.lower()

    # Safety rule: do not allow warehouse data modifications
    unsafe_actions = ["release", "cancel", "change", "update", "modify"]

    if any(action in query for action in unsafe_actions):
        return (
            "I can provide warehouse information and recommendations, "
            "but I cannot modify orders, inventory, or perform warehouse transactions. "
            "Please contact an authorized warehouse operator."
        )

    # Basic keyword-based responses
    if "order" in query:
        return (
            "I can help with order-related questions, but this baseline version "
            "cannot retrieve actual order information."
        )

    elif "inventory" in query or "stock" in query:
        return (
            "I can help with inventory-related questions, but this baseline version "
            "cannot check actual inventory availability."
        )

    elif "sop" in query or "procedure" in query:
        return (
            "I can help with warehouse procedures, but this baseline version "
            "cannot search the warehouse SOP."
        )

    else:
        return (
            "I could not understand the request using the available rules. "
            "Please provide more details."
        )


def log_interaction(user_query, response):
    """
    Save the interaction to a local log file.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("baseline_interactions.log", "a") as log_file:
        log_file.write(f"{timestamp}\n")
        log_file.write(f"User: {user_query}\n")
        log_file.write(f"Agent: {response}\n")
        log_file.write("-" * 50 + "\n")


def main():
    print("=" * 55)
    print("Warehouse Operations AI Copilot - Baseline Agent")
    print("=" * 55)
    print("Type 'exit' to close the application.\n")

    while True:
        user_query = input("You: ")

        if user_query.lower() == "exit":
            print("Agent: Goodbye!")
            break

        response = get_baseline_response(user_query)

        print(f"Agent: {response}\n")

        log_interaction(user_query, response)


if __name__ == "__main__":
    main()