import json
import logging
from collections.abc import Iterator, MutableMapping
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    pass


class ConfigLoader(MutableMapping):
    """
    Loads and provides read-only access to a JSON or YAML configuration file.

    Features:
      - Supports JSON (and optionally YAML if PyYAML installed).
      - Mapping interface: dict-like access and iteration.
      - Dot-separated nested key lookup via .get(key, default).
      - Automatic reloading via .reload().
      - Optional environment-variable expansion in string values.
    """

    def __init__(
        self,
        filepath: Path | str,
        *,
        env_expand: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        self.filepath = Path(filepath)
        self.env_expand = env_expand
        self.logger = logger or logging.getLogger(__name__)
        self._data: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """
        Reload the configuration file into memory.
        Raises ConfigError if the file is missing or malformed.
        """
        if not self.filepath.exists():
            raise ConfigError(f"Configuration file not found: {self.filepath}")
        text = self.filepath.read_text(encoding="utf-8")
        try:
            if self.filepath.suffix.lower() in [".yaml", ".yml"]:
                import yaml

                data = yaml.safe_load(text)
            elif self.filepath.suffix.lower() == ".json":
                data = json.loads(text)
            else:
                raise ConfigError("Configuration root must be a JSON/YAML object")

            self._data = data
            self.logger.debug(f"Loaded config from {self.filepath}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON syntax error in {self.filepath}: {e}") from e
        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError(f"Error loading config: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value by key.
        Supports dot notation for nested dictionaries.
        Expands environment variables if env_expand=True and value is a string.
        """
        parts = key.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        if self.env_expand and isinstance(current, str):
            from os import path

            # expand ${VAR} and ~ for homedir
            return path.expanduser(path.expandvars(current))
        return current

    # Required by MutableMapping:
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("ConfigLoader is read-only")

    def __delitem__(self, key: str) -> None:
        raise TypeError("ConfigLoader is read-only")

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def copy(self) -> "ConfigLoader":
        """
        Return a shallow, in-memory copy that still supports dot-notation .get().

        MutableMapping doesn't provide .copy(), and a plain dict.copy() would
        silently break callers relying on dot-notation lookups, so this builds
        a new ConfigLoader without re-reading filepath from disk.
        """
        new = ConfigLoader.__new__(ConfigLoader)
        new.filepath = self.filepath
        new.env_expand = self.env_expand
        new.logger = self.logger
        new._data = dict(self._data)
        return new
