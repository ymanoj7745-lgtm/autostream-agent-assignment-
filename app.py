import os
import random
import time

from dotenv import load_dotenv

from graph import build_agent
from state import create_initial_state


def main() -> None:
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file.")

    agent, _client = build_agent()
    state = create_initial_state()

    print("AutoStream Agent is ready. Type 'exit' to stop.\n")

    while True:
        user_message = input("You: ").strip()
        if not user_message:
            continue
        if user_message.lower() == "exit":
            print("Agent: Goodbye!")
            break

        state["pending_user_message"] = user_message
        state["messages"] = state["messages"] + [{"role": "user", "content": user_message}]
        result = agent.invoke(state)
        answer = result["answer"]

        state.update(result)
        state["messages"] = state["messages"] + [{"role": "assistant", "content": answer}]
        state["pending_user_message"] = ""

        time.sleep(random.uniform(0.9, 1.6))
        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    main()
