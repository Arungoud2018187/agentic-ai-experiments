from tools.database_tool import initialize_database
from tools.schema_tool import get_schema
from agent.graph import run_agent


def main():

    print("=" * 60)
    print("           SQL AGENT WITH TOOL USE")
    print("=" * 60)

    initialize_database()

    print("\nDatabase initialized.")

    print("\nAvailable schema:")
    print("-" * 60)
    print(get_schema())

    print("\nType 'exit' to quit.")

    while True:

        question = input(
            "\nAsk the SQL Agent: "
        ).strip()

        if question.lower() == "exit":

            print("Exiting...")

            break

        if not question:
            continue

        try:

            state = run_agent(
                question
            )

            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)

            print(state.answer)

        except Exception as error:

            print("\nAGENT ERROR:")
            print(error)


if __name__ == "__main__":
    main()