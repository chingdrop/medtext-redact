import pandas as pd
import pytest

from vega_tools.core.pandas_tools import (
    audit_images,
    check_series_by_study,
    create_project_comparison,
    find_column_for_value,
    merge_on_matched_column,
    read_structured_file,
    repackage_txts_to_csv,
    search_column_for_keywords,
    search_report_text,
    split_csv_to_txt,
    write_structured_file,
)


class TestReadStructuredFile:
    def test_reads_csv(self, tmp_path):
        path = tmp_path / "data.csv"
        pd.DataFrame({"a": [1, 2]}).to_csv(path, index=False)
        df = read_structured_file(path)
        assert list(df["a"]) == [1, 2]

    def test_reads_xlsx(self, tmp_path):
        path = tmp_path / "data.xlsx"
        pd.DataFrame({"a": [1, 2]}).to_excel(path, index=False, engine="openpyxl")
        df = read_structured_file(path)
        assert list(df["a"]) == [1, 2]

    def test_reads_json(self, tmp_path):
        path = tmp_path / "data.json"
        pd.DataFrame({"a": [1, 2]}).to_json(path)
        df = read_structured_file(path)
        assert list(df["a"]) == [1, 2]

    def test_unsupported_extension_returns_none(self, tmp_path):
        path = tmp_path / "data.parquet"
        path.write_text("irrelevant")
        assert read_structured_file(path) is None

    def test_file_type_override(self, tmp_path):
        path = tmp_path / "data.weird"
        pd.DataFrame({"a": [1]}).to_csv(path, index=False)
        df = read_structured_file(path, file_type="csv")
        assert list(df["a"]) == [1]

    def test_missing_file_returns_none_instead_of_raising(self, tmp_path):
        assert read_structured_file(tmp_path / "missing.csv") is None


class TestWriteStructuredFile:
    def test_writes_csv(self, tmp_path):
        path = tmp_path / "out.csv"
        ok = write_structured_file(pd.DataFrame({"a": [1, 2]}), path, index=False)
        assert ok is True
        assert path.exists()

    def test_unsupported_extension_returns_false(self, tmp_path):
        path = tmp_path / "out.parquet"
        assert write_structured_file(pd.DataFrame({"a": [1]}), path) is False
        assert not path.exists()

    def test_write_error_returns_false(self, tmp_path):
        # Directory as the target path is not a writable file location.
        bad_path = tmp_path / "adir.csv"
        bad_path.mkdir()
        assert write_structured_file(pd.DataFrame({"a": [1]}), bad_path) is False


class TestSearchColumnForKeywords:
    def test_extracts_matching_keyword(self):
        series = pd.Series(["left breast biopsy", "right knee scan", "no match here"])
        result = search_column_for_keywords(series, ["left", "right"])
        assert isinstance(result, pd.Series)
        assert result[0] == "left"
        assert result[1] == "right"
        assert pd.isna(result[2])


class TestSearchReportText:
    def test_adds_expected_columns(self):
        df = pd.DataFrame({"ReportText": ["left biopsy benign carcinoma"]})
        config = {
            "Searching": {
                "AnatomicalTags": ["left", "right"],
                "PathologyKeywords": ["carcinoma"],
            }
        }
        result = search_report_text(df, config)
        assert result.loc[0, "FoundBiopsySide"] == "left"
        assert result.loc[0, "FoundBiopsyResult"] == "benign"
        assert result.loc[0, "FoundPathologyType"] == "carcinoma"


class TestCheckSeriesByStudy:
    def test_found_when_all_descriptions_present(self):
        df = pd.DataFrame(
            {
                "Accession": ["A1", "A1"],
                "Series": ["X", "Y"],
            }
        )
        result = check_series_by_study(df, "Accession", "Series", {"X", "Y"})
        row = result.iloc[0]
        assert row["Status"] == "Found"
        assert pd.isna(row["Missing Set"])

    def test_missing_when_description_absent(self):
        df = pd.DataFrame(
            {
                "Accession": ["A1"],
                "Series": ["X"],
            }
        )
        result = check_series_by_study(df, "Accession", "Series", {"X", "Y"})
        row = result.iloc[0]
        assert row["Status"] == "Missing"
        assert row["Missing Set"] == {"Y"}

    def test_one_row_per_accession(self):
        df = pd.DataFrame(
            {
                "Accession": ["A1", "A1", "A2"],
                "Series": ["X", "Y", "X"],
            }
        )
        result = check_series_by_study(df, "Accession", "Series", {"X"})
        assert len(result) == 2


class TestAuditImages:
    def _base_df(self):
        return pd.DataFrame(
            {
                "Accession": ["A1", "A1", "A2"],
                "Series Description": ["2D-VIEW", "3D-VOL", "2D-VIEW"],
                "Number of Frames": [1, 3, 1],
                "Slice Thickness": [0, 1, 0],
            }
        )

    def test_2d_filters_single_frame_series(self):
        result = audit_images(self._base_df(), "2D", {"2D-VIEW"})
        assert set(result["Accession"]) == {"A1", "A2"}
        assert (result["Image Type"] == "2D").all()

    def test_3d_filters_on_frames_and_thickness(self):
        result = audit_images(self._base_df(), "3D", {"3D-VOL"}, slice_thickness=1)
        assert list(result["Accession"]) == ["A1"]
        assert result.iloc[0]["Image Type"] == "3D"

    def test_invalid_img_type_raises(self):
        with pytest.raises(ValueError):
            audit_images(self._base_df(), "4D", {"X"})


class TestFindColumnForValue:
    def test_finds_column_containing_value(self):
        df = pd.DataFrame({"a": ["x", "y"], "b": ["z", "ACC1"]})
        assert find_column_for_value(df, "ACC1") == "b"

    def test_returns_none_when_not_found(self):
        df = pd.DataFrame({"a": ["x", "y"]})
        assert find_column_for_value(df, "missing") is None

    def test_returns_first_matching_column(self):
        df = pd.DataFrame({"a": ["v"], "b": ["v"]})
        assert find_column_for_value(df, "v") == "a"


class TestMergeOnMatchedColumn:
    def test_merges_matched_row_data(self):
        result_df = pd.DataFrame({"accession": ["ACC1"], "matched_col": ["colB"]})
        data_df = pd.DataFrame({"colA": ["x", "y"], "colB": ["z", "ACC1"]})

        merged = merge_on_matched_column(result_df, data_df, key_col="accession", matched_col_col="matched_col")

        assert merged.loc[0, "colA"] == "y"
        assert merged.loc[0, "colB"] == "ACC1"

    def test_no_matched_columns_returns_copy_of_result(self):
        result_df = pd.DataFrame({"accession": ["ACC1"], "matched_col": [None]})
        data_df = pd.DataFrame({"colA": ["x"]})

        merged = merge_on_matched_column(result_df, data_df)

        assert merged.equals(result_df)
        assert merged is not result_df


class TestCreateProjectComparison:
    def test_orders_by_parsed_project_name(self):
        df = pd.DataFrame(
            {
                "file_1": ["vega-200"],
                "file_2": ["vega-100"],
                "file_1_accession": ["ACC2"],
                "file_2_accession": ["ACC1"],
                "study_instance_uid": ["UID1"],
            }
        )
        result = create_project_comparison(df)
        assert result.iloc[0]["project_1"] == "vega-100"
        assert result.iloc[0]["project_2"] == "vega-200"
        assert result.iloc[0]["accession_1"] == "ACC1"
        assert result.iloc[0]["accession_2"] == "ACC2"

    def test_already_ordered_stays_in_place(self):
        df = pd.DataFrame(
            {
                "file_1": ["vega-100"],
                "file_2": ["vega-200"],
                "file_1_accession": ["ACC1"],
                "file_2_accession": ["ACC2"],
                "study_instance_uid": ["UID1"],
            }
        )
        result = create_project_comparison(df)
        assert result.iloc[0]["project_1"] == "vega-100"
        assert result.iloc[0]["project_2"] == "vega-200"


class TestSplitCsvToTxt:
    def test_writes_one_txt_file_per_accession(self, tmp_path):
        csv_path = tmp_path / "sample.csv"
        pd.DataFrame(
            {
                "Accession": ["ACC001", "ACC002"],
                "Reports": ["Report one text", "Report two text"],
            }
        ).to_csv(csv_path, index=False)
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        split_csv_to_txt(csv_path, output_dir)

        assert (output_dir / "ACC001.txt").read_text(encoding="utf-8") == "Report one text"
        assert (output_dir / "ACC002.txt").read_text(encoding="utf-8") == "Report two text"

    def test_strips_whitespace_from_accession(self, tmp_path):
        csv_path = tmp_path / "sample.csv"
        pd.DataFrame(
            {
                "Accession": [" ACC001 "],
                "Reports": ["text"],
            }
        ).to_csv(csv_path, index=False)
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        split_csv_to_txt(csv_path, output_dir)

        assert (output_dir / "ACC001.txt").exists()


class TestRepackageTxtsToCsv:
    def test_round_trips_txt_files_into_csv(self, tmp_path):
        input_dir = tmp_path / "in"
        input_dir.mkdir()
        (input_dir / "ACC001.txt").write_text("de-identified text", encoding="utf-8")
        csv_path = tmp_path / "result.csv"

        repackage_txts_to_csv(input_dir, csv_path)

        result = pd.read_csv(csv_path)
        assert result.iloc[0]["Filename"] == "ACC001"
        assert result.iloc[0]["Contents"] == "de-identified text"
