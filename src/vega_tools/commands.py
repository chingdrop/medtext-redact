import click
import re
from pathlib import Path

from vega_tools.text_parser import ReportWriter
from vega_tools.utils.files_and_storage import write_text_to_file


@click.command()
def main():
    data_dir = Path.cwd() / 'data'
    with open(data_dir / 'report_text.txt', 'r') as f:
        text = f.read()

    rw = ReportWriter(text)
    rw.sanitize_dates()
    rw.sanitize_age()
    rw.sanitize_keywords(['female', 'male'], '******')
    # Medical supplies names
    rw.sanitize_keywords(['hydromark', 'marquee', 'suros celeros', 'suros eviva'], '********')
    penrad_pattern = re.compile(r'[a-zA-Z]{2,3}/Penrad', flags=re.IGNORECASE)
    rw.text = penrad_pattern.sub('***/******', rw.text)
    # Medical location names
    rw.sanitize_keywords(
        ['Laboratory For Pathological Analysis'], '*********** For ************ *********'
    )
    rw.sanitize_keywords(
        [
            'Southside Imaging Center - Radiology Associates',
            'Portland Imaging Center - Radiology Associates',
            'Six Points Office - Radiology Associates'
        ],
        '********* ******* ****** - ********* *********'
    )
    # ToDo - Find a way to reference a database of common names, instead of manually filling what you find.
    rw.sanitize_keywords(
        [
            'Michael',
            'Wayne',
            'Michell',
            'Mailan',
            'Melissa',
            'Cao',
            'Kenneth',
            'Cook',
            'Turner',
            'Jennifer',
            'Christopher',
            'Thomas',
            'Bruce'
        ], '********'
    )

    write_text_to_file(rw.text, data_dir / 'new_report_text.txt')

    print(('-' * 79), '\n')
    # Keywords were found from initially skimming the report
    rw.print_line_with_keywords(['left'])
    rw.print_line_with_keywords(['right'])
    rw.print_line_with_keywords(['wire', 'localization'])
    rw.print_line_with_keywords(['benign'])
    rw.print_line_with_keywords(['malignant'])
    rw.print_line_with_keywords(['results'])
    rw.print_line_with_keywords(['impression'])
    rw.print_line_with_keywords(['pathology'])
