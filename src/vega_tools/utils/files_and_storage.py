from pathlib import Path


def write_text_to_file(text: str, path: Path | str) -> None:
    """
    Writes a string to a file.

    Args:
        text (str): String content to be written to file.
        path (str | Path): Path of the file to be written.
    """
    try:
        with open(path, 'w') as f:
            f.write(text)
    except (OSError, IOError) as e:
        print(f"Error writing to file '{path}': {e}")


def read_text_from_file(path: Path | str) -> str | None:
    """
    Reads a file into a string.

    Args:
        path (str | Path): Path of the file to be written.

    Returns:
        str | None: String content read from file.
    """
    try:
        with open(path, 'r') as f:
            return f.read()
    except (OSError, IOError) as e:
        print(f"Error reading file '{path}': {e}")
        return None