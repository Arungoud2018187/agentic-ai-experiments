from src.chain import run_chain


def main():

    print("=" * 60)
    print("             PROMPT CHAINING SYSTEM")
    print("=" * 60)

    print("\nEnter text to analyze.")
    print("Type 'END' on a new line when finished.")
    print("Type 'exit' to quit.\n")

    while True:

        lines = []

        while True:

            line = input()

            if line.lower() == "exit":
                return

            if line == "END":
                break

            lines.append(line)

        text = "\n".join(lines).strip()

        if not text:
            print("No text provided.")
            continue

        try:

            result = run_chain(text)

            print("\n" + "=" * 60)
            print("STEP 1 — EXTRACTED INFORMATION")
            print("=" * 60)
            print(result["information"])

            print("\n" + "=" * 60)
            print("STEP 2 — ANALYSIS")
            print("=" * 60)
            print(result["analysis"])

            print("\n" + "=" * 60)
            print("STEP 3 — SUMMARY")
            print("=" * 60)
            print(result["summary"])

            print("\n" + "=" * 60)
            print("STEP 4 — FINAL OUTPUT")
            print("=" * 60)
            print(result["final_output"])

        except Exception as error:

            print("\nERROR:")
            print(error)


if __name__ == "__main__":
    main()