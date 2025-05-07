from pathlib import Path


def write_text_to_file(text: str, filepath: Path | str) -> None:
    """
    Writes a string to a file.

    Args:
        text (str): String content to be written to file.
        filepath (str | Path): Path of the file to be written.
    """
    try:
        with open(filepath, 'w') as file:
            file.write(text)
    except (OSError, IOError) as e:
        print(f"Error writing to file '{filepath}': {e}")


def read_text_from_file(filepath: Path | str) -> str | None:
    """
    Reads a file into a string.

    Args:
        filepath (str | Path): Path of the file to be written.

    Returns:
        str | None: String content read from file.
    """
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except (OSError, IOError) as e:
        print(f"Error reading file '{filepath}': {e}")
        return None


# ToDo - Add docstring for function.
def create_directory(filepath: Path | str) -> None:
    if isinstance(filepath, str):
        filepath = Path(filepath)
    filepath.mkdir(parents=True, exist_ok=True)
