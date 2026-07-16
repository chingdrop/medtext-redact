import json

import pytest

from vega_tools.core.utils.config_loader import ConfigError, ConfigLoader


def write_json(tmp_path, data, name="config.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestLoading:
    def test_loads_json_config(self, tmp_path):
        path = write_json(tmp_path, {"a": 1})
        loader = ConfigLoader(path)
        assert loader["a"] == 1

    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError):
            ConfigLoader(tmp_path / "missing.json")

    def test_malformed_json_raises_config_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ConfigError):
            ConfigLoader(path)

    def test_unsupported_extension_raises_config_error(self, tmp_path):
        path = tmp_path / "config.txt"
        path.write_text("{}", encoding="utf-8")
        with pytest.raises(ConfigError):
            ConfigLoader(path)

    def test_yaml_config_loads_if_pyyaml_available(self, tmp_path):
        yaml = pytest.importorskip("yaml")
        path = tmp_path / "config.yaml"
        path.write_text("a: 1\n", encoding="utf-8")
        loader = ConfigLoader(path)
        assert loader["a"] == 1
        assert yaml  # silence unused-import warning if importorskip succeeds


class TestGet:
    def test_get_top_level_key(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        assert loader.get("a") == 1

    def test_get_nested_dot_notation(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"Masking": {"Manufacturers": ["GE"]}}))
        assert loader.get("Masking.Manufacturers") == ["GE"]

    def test_get_missing_key_returns_default(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        assert loader.get("missing", "fallback") == "fallback"

    def test_get_missing_key_returns_none_by_default(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        assert loader.get("missing") is None

    def test_get_partial_nested_path_missing_returns_default(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"Masking": {}}))
        assert loader.get("Masking.Manufacturers", []) == []

    def test_env_expand_expands_environment_variables(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_VAR", "expanded")
        loader = ConfigLoader(write_json(tmp_path, {"path": "${MY_VAR}/x"}), env_expand=True)
        assert loader.get("path") == "expanded/x"

    def test_env_expand_false_leaves_value_literal(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_VAR", "expanded")
        loader = ConfigLoader(write_json(tmp_path, {"path": "${MY_VAR}/x"}), env_expand=False)
        assert loader.get("path") == "${MY_VAR}/x"


class TestMappingInterface:
    def test_getitem(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        assert loader["a"] == 1

    def test_setitem_raises_type_error(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        with pytest.raises(TypeError):
            loader["a"] = 2

    def test_delitem_raises_type_error(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        with pytest.raises(TypeError):
            del loader["a"]

    def test_iter_and_len(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1, "b": 2}))
        assert len(loader) == 2
        assert set(iter(loader)) == {"a", "b"}

    def test_copy_returns_independent_config_loader(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1, "b": 2}))
        copied = loader.copy()
        assert copied is not loader
        assert isinstance(copied, ConfigLoader)
        assert dict(copied) == {"a": 1, "b": 2}

    def test_copy_preserves_dot_notation_get(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"Masking": {"Manufacturers": ["GE"]}}))
        copied = loader.copy()
        assert copied.get("Masking.Manufacturers") == ["GE"]

    def test_copy_mutation_does_not_affect_original(self, tmp_path):
        loader = ConfigLoader(write_json(tmp_path, {"a": 1}))
        copied = loader.copy()
        copied._data["a"] = 2
        assert loader["a"] == 1


class TestReload:
    def test_reload_picks_up_file_changes(self, tmp_path):
        path = write_json(tmp_path, {"a": 1})
        loader = ConfigLoader(path)
        assert loader["a"] == 1

        path.write_text(json.dumps({"a": 2}), encoding="utf-8")
        loader.reload()
        assert loader["a"] == 2
