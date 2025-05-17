import logging
from pathlib import Path
from typing import Union, Optional


logger = logging.getLogger(__name__)

def write_text_to_file(
    text: str,
    filepath: Union[Path, str],
    *,
    encoding: str = "utf-8",
    overwrite: bool = True
) -> Path:
    """
    Write a string to a file, creating parent directories as needed.

    Args:
        text:       Content to write.
        filepath:   Target file path.
        encoding:   File encoding (default: utf-8).
        overwrite:  If False and the file exists, raises FileExistsError.

    Returns:
        The Path to which the text was written.

    Raises:
        FileExistsError
        OSError
    """
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not overwrite and path.exists():
            msg = f"File already exists and overwrite is False: {path}"
            logger.error(msg)
            raise FileExistsError(msg)

        path.write_text(text, encoding=encoding)
        logger.debug(f"Wrote text to {path}, {encoding}")
        return path

    except Exception as e:
        logger.exception(f"Failed to write text to {path}: {e}")
        raise


def read_text_from_file(
    filepath: Union[Path, str],
    *,
    encoding: str = "utf-8"
) -> str:
    """
    Read an entire text file into a string.

    Args:
        filepath:  Path to the file.
        encoding:  File encoding (default: utf-8).

    Returns:
        The file’s contents as a string.

    Raises:
        FileNotFoundError
        OSError
    """
    path = Path(filepath)
    try:
        content = path.read_text(encoding=encoding)
        logger.debug(f"Read {len(content)} characters from {path}, {encoding}")
        return content

    except Exception as e:
        logger.exception(f"Failed to read text from {path}: {e}")
        raise


def create_directory(
    dirpath: Union[Path, str],
    *,
    exist_ok: bool = True
) -> Path:
    """
    Ensure a directory exists, creating it (and parents) if necessary.

    Args:
        dirpath:   Directory to create.
        exist_ok:  If False and dir exists, raises FileExistsError.

    Returns:
        The Path of the directory.

    Raises:
        FileExistsError
        OSError
    """
    path = Path(dirpath)
    try:
        path.mkdir(parents=True, exist_ok=exist_ok)
        logger.debug(f"Created directory {path}, exist_ok is {exist_ok}")
        return path

    except Exception as e:
        logger.exception(f"Failed to create directory {path}: {e}")
        raise
