import pytest

from vega_tools.core.utils.files_and_storage import create_directory, read_text_from_file, write_text_to_file


class TestWriteTextToFile:
    def test_writes_text_and_returns_path(self, tmp_path):
        target = tmp_path / "out.txt"
        result = write_text_to_file("hello", target)
        assert result == target
        assert target.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / "nested" / "dir" / "out.txt"
        write_text_to_file("hello", target)
        assert target.exists()

    def test_overwrite_true_replaces_existing_content(self, tmp_path):
        target = tmp_path / "out.txt"
        write_text_to_file("first", target)
        write_text_to_file("second", target)
        assert target.read_text() == "second"

    def test_overwrite_false_raises_if_file_exists(self, tmp_path):
        target = tmp_path / "out.txt"
        write_text_to_file("first", target)
        with pytest.raises(FileExistsError):
            write_text_to_file("second", target, overwrite=False)

    def test_overwrite_false_succeeds_if_file_missing(self, tmp_path):
        target = tmp_path / "out.txt"
        write_text_to_file("first", target, overwrite=False)
        assert target.read_text() == "first"


class TestReadTextFromFile:
    def test_reads_written_content(self, tmp_path):
        target = tmp_path / "in.txt"
        target.write_text("some content", encoding="utf-8")
        assert read_text_from_file(target) == "some content"

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_text_from_file(tmp_path / "does-not-exist.txt")

    def test_accepts_string_path(self, tmp_path):
        target = tmp_path / "in.txt"
        target.write_text("content")
        assert read_text_from_file(str(target)) == "content"


class TestCreateDirectory:
    def test_creates_directory(self, tmp_path):
        target = tmp_path / "newdir"
        result = create_directory(target)
        assert result == target
        assert target.is_dir()

    def test_creates_nested_parents(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        create_directory(target)
        assert target.is_dir()

    def test_exist_ok_true_is_idempotent(self, tmp_path):
        target = tmp_path / "newdir"
        create_directory(target)
        create_directory(target, exist_ok=True)
        assert target.is_dir()

    def test_exist_ok_false_raises_if_exists(self, tmp_path):
        target = tmp_path / "newdir"
        create_directory(target)
        with pytest.raises(FileExistsError):
            create_directory(target, exist_ok=False)
