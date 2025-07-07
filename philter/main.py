import os
import nltk
import pandas as pd
from pathlib import Path


nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')

base_path = Path(__file__).resolve().parent
data_path = base_path / 'data'
input_path = data_path / 'input'
output_path = data_path / 'output'


def split_csv_to_txt(csv_path, output_path):
    """
    Read a CSV and write each 'Reports' field to a separate text file
    named <Accession>.txt under output_dir.
    """
    output_path.mkdir(parents=True, exist_ok=True)

    # Read only what we need, force strings so NaNs become 'nan' not float
    df = pd.read_csv(csv_path, usecols=['Accession', 'Reports'], dtype=str)

    for accession, report in df.itertuples(index=False):
        accession = accession.strip()   # sanitize whitespace
        report = report or ''           # guard against None/NaN
        outfile = output_path / f"{accession}.txt"
        print(f"Writing report for Accession: {accession}")
        outfile.write_text(report, encoding='utf-8')


def repackage_into_csv(result_report):
    data = []
    for filename in os.listdir(output_path):
        if filename.endswith(".txt"):
            with open(os.path.join(output_path, filename), 'r') as f:
                contents = f.read()

            data.append((filename, contents))

    df = pd.DataFrame(data, columns=['Filename', 'Contents'])
    df['Filename'] = df['Filename'].str.replace('.txt', '', regex=False)
    df.to_csv(result_report, index=False)


def main():
    original_report_path = data_path / 'original_reports.csv'
    result_report = data_path / 'result_report.csv'
    philter_base_path = base_path / 'philter-ucsf'
    philter_delta_path = philter_base_path / 'configs' / 'philter_delta.json'

    split_csv_to_txt(original_report_path, input_path)
    os.chdir(philter_base_path)
    os.system(f'python main.py -i {input_path} -o {output_path} -f {philter_delta_path} --prod=True --outputformat "asterisk"')
    repackage_into_csv(result_report)
    print("Done...")


if __name__ == "__main__":
    main()