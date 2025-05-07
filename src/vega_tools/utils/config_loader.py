import json
from pathlib import Path


# ToDo - Add docstrings for class.
class ConfigLoader:
    def __init__(self, filepath: Path | str):
        if isinstance(filepath, str):
            filepath = Path(filepath)
        self.filepath = filepath
        self.config = self._load()

    def _load(self):
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
