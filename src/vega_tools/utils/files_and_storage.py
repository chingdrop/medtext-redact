from pathlib import Path


def write_text_to_file(text: str, filename: Path | str) -> None:
    with open(filename, 'w') as f:
        f.write(text)


def read_text_from_file(filename: Path | str) -> str:
    with open(filename, 'r') as f:
        return f.read()