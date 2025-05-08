import json
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """
    Loads a JSON configuration file to a dictionary.

    Args:
        filepath (Path | str): File path to configuration file.

    Attributes:
        config (dict): The configuration dictionary.
    """

    def __init__(self, filepath: Path | str):
        if isinstance(filepath, str):
            filepath = Path(filepath)
        self.filepath = filepath
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        """
        Loads the configuration file into a dictionary from a JSON file.

        Returns:
            Dict[str, Any]: The configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file is malformed.
        """
        if not self.filepath.exists():
            raise FileNotFoundError(f"Config file not found: {self.filepath}")
        with open(self.filepath, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON error: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def as_kwargs(self):
        return self.config
