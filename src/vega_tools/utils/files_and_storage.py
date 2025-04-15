from pathlib import Path


def write_text_to_file(text: str, filename: Path | str) -> None:
    with open(filename, 'w') as f:
        f.write(text)