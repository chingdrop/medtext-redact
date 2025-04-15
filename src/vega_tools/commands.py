import click
from pathlib import Path

from vega_tools.text_tools import print_line_with_keywords
from vega_tools.pandas_tools import read_excel_file, white_rabbit_parse_report
from vega_tools.utils.files_and_storage import read_text_from_file, write_text_to_file


@click.command()
def console():
    data_dir = Path.cwd() / 'data'
    text = read_text_from_file(Path.cwd() / 'data' / 'text.txt')

    result_text = white_rabbit_parse_report(text)
    write_text_to_file(result_text, data_dir / 'new_report_text.txt')

    print(('-' * 104), '\n')
    # Keywords were found from initially skimming the report
    print_line_with_keywords(['left'], result_text)
    print_line_with_keywords(['right'], result_text)
    print_line_with_keywords(['wire', 'localization'], result_text)
    print_line_with_keywords(['benign'], result_text)
    print_line_with_keywords(['malignant'], result_text)
    print_line_with_keywords(['results'], result_text)
    print_line_with_keywords(['impression'], result_text)
    print_line_with_keywords(['pathology'], result_text)


@click.command()
def main():
    df = read_excel_file(Path.cwd() / 'data' / "PRJ116405_ClientFacing_Reference_SpreadsheetvB.xlsx")
    result_df = df[(df['StudyDescription'] == 'BIOPSY') & (df['ExamCategory'] == 'Biopsy')]
    result_df = result_df[[
        'Accession',
        'Original PID',
        'Orig BX Date',
        'ReportText',
        'BiopsyDate',
        'BiopsySide',
        'BiopsyResult',
        'PathologyType'
    ]]
    result_df = result_df['ReportText'].apply(white_rabbit_parse_report)
    result_df.to_excel(Path.cwd() / 'data' / 'result_reports.xlsx')
