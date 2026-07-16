import click
import numpy as np
import pandas as pd

from vega_tools.core.pandas_tools import (
    read_structured_file,
    write_structured_file,
    audit_images,
    find_column_for_value,
    merge_on_matched_column,
    create_project_comparison,
)
from vega_tools.core.utils.enums import DICOM_2D_SERIES_DESCRIPTIONS, DICOM_3D_SERIES_DESCRIPTIONS
from vega_tools.paths import DATA_DIRECTORY


@click.command()
@click.option("--project", "-p", help="Project tag to filter from the reference spreadsheet.")
@click.option("--sample", "-s", type=click.Path(exists=True), help="File path to Sample Spreadsheet")
@click.option("--result", "-r", type=click.Path(), help="File path to Result Spreadsheet")
@click.option(
    "--order",
    "-o",
    type=click.Choice(["first", "second"], case_sensitive=False),
    help="Choose which project order to use",
)
def validate_studies(project, sample, result, order):
    if order == "first":
        proj_col = "project_1"
        access_col = "accession_1"
    else:
        proj_col = "project_2"
        access_col = "accession_2"

    ref_df = read_structured_file(DATA_DIRECTORY / "dupe_audit.xlsx")
    ref_df = ref_df[ref_df[proj_col] == project]

    data_df = read_structured_file(sample)
    matched_col = ref_df[access_col].apply(lambda x: find_column_for_value(data_df, x))
    result_df = pd.DataFrame(
        {
            "study_instance_uid": ref_df["study_instance_uid"],
            "accession": ref_df[access_col],
            "matched_col": matched_col,
        }
    )
    result_df["failure"] = result_df["matched_col"] == "Failure Not Found"
    result_df["type"] = np.where(result_df["matched_col"].str.contains("prior", case=False, na=False), "Prior", "Index")
    result_df = merge_on_matched_column(result_df, data_df, key_col="accession", matched_col_col="matched_col")

    keep_columns = ["study_instance_uid", "accession", "matched_col", "failure", "type"]
    group_columns = [col for col in result_df.columns if "group" in str(col).lower()]
    final_columns = keep_columns + group_columns
    result_df = result_df[final_columns]
    write_structured_file(result_df, result, index=False)


@click.command()
@click.option("--sample", "-s", type=click.Path(exists=True), help="File path to Sample Spreadsheet")
@click.option("--result", "-r", type=click.Path(), help="File path to Result Spreadsheet")
def compare_projects(sample, result):
    data_df = read_structured_file(sample)
    result_df = create_project_comparison(data_df)
    write_structured_file(result_df, result, index=False)


@click.command()
@click.option("--sample", "-s", type=click.Path(exists=True), help="File path to Sample Spreadsheet")
@click.option("--result", "-r", type=click.Path(), help="File path to Result Spreadsheet")
def audit_series_by_study(sample, result):
    data_df = read_structured_file(sample)
    data_df.replace("<NONE>", np.nan, inplace=True)
    data_df.drop("File", axis=1, inplace=True)
    data_df.rename(
        columns={
            "0008:0050": "Accession",
            "0010:0020": "PID",
            "0008:0018": "SOP Instance UID",
            "0008:0008": "Image Type",
            "0028:0008": "Number of Frames",
            "0020:0062": "Image Laterality (2D Only)",
            "5200:9229.#0.0020:9071.#0.0020:9072": "Frame Laterality (3D Only)",
            "5200:9229.#0.0028:9110.#0.0018:0050": "Slice Thickness",
            "0054:0220.#0.0008:0100": "View Code",
            "0054:0220.#0.0054:0222.#0.0008:0100": "View Modifier Code",
            "0008:0070": "Manufacturer",
            "0008:1090": "Model",
            "0008:103E": "Series Description",
            "0008:1030": "Study Description",
            "0002:0010": "Transfer Syntax",
        },
        inplace=True,
    )
    audit_2d_df = audit_images(data_df, "2D", DICOM_2D_SERIES_DESCRIPTIONS)
    audit_3d_df = audit_images(data_df, "3D", DICOM_3D_SERIES_DESCRIPTIONS, 1)
    audit_df = pd.concat([audit_2d_df, audit_3d_df])
    audit_df.sort_values(["Accession"], inplace=True)
    write_structured_file(audit_df, result, index=False)
