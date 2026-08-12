from src.database import initialize_database
from src.schema import get_database_schema
from src.sql_generator import generate_sql
from src.executor import execute_sql


def main():

    print("=" * 60)
    print("        TEXT-TO-SQL LLM SYSTEM")
    print("=" * 60)

    # Create database
    initialize_database()

    # Get database schema
    schema = get_database_schema()

    print("\nDatabase Schema:")
    print("-" * 60)
    print(schema)

    print("\nType 'exit' to quit.")

    while True:

        question = input("\nAsk a database question: ").strip()

        if question.lower() == "exit":
            print("Exiting...")
            break

        if not question:
            continue

        try:

            print("\nGenerating SQL...")

            sql = generate_sql(
                question,
                schema
            )

            print("\nGenerated SQL:")
            print("-" * 60)
            print(sql)

            print("\nExecuting SQL...")

            results = execute_sql(sql)

            print("\nResults:")
            print("-" * 60)

            if not results:
                print("No results found.")

            else:
                for row in results:
                    print(row)

        except Exception as error:

            print("\nERROR:")
            print(error)


if __name__ == "__main__":
    main()