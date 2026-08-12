from pathlib import Path


def load_documents(data_directory="data"):

    data_path = Path(data_directory)

    documents = []

    for file_path in data_path.glob("*.txt"):

        text = file_path.read_text(
            encoding="utf-8"
        )

        documents.append({
            "filename": file_path.name,
            "text": text
        })

    return documents