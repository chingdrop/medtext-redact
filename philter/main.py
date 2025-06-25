# Import key operating system functionality
import os
import pandas as pd
from pathlib import Path


base_path = Path(__file__).resolve().parent

data_path = base_path / 'data'
input_path = data_path / 'input'
output_path = data_path / 'output'

philter_base_path = base_path / 'philter-ucsf'
philter_delta_path = philter_base_path / 'configs' / 'philter_delta.json'


def csv_splitter(original_report):
    df = pd.read_csv(original_report)
    for index, row in df.iterrows():
        accession = str(row['Accession'])
        report = str(row['Reports'])
        os.chdir(input_path)
        print(f"Converting file: {accession}")
        with open(f'{accession}.txt', 'w') as f:
            f.write(report)


def repackage_into_csv(result_report):
    data = []
    for filename in os.listdir(output_path):
        if filename.endswith(".txt"):
            with open(os.path.join(output_path, filename), 'r') as f:
                contents = f.read()

            data.append((filename, contents))

    df = pd.DataFrame(data, columns=['Filename', 'Contents'])
    df.to_csv(result_report, index=False)


def main():
    original_report_path = data_path / 'original_reports.csv'
    result_report = data_path / 'result_report.csv'

    csv_splitter(original_report_path)

    os.chdir(philter_base_path)
    os.system(f'python main.py -i {input_path} -o {output_path} -f {philter_delta_path} --prod=True --outputformat "asterisk"')

    repackage_into_csv(result_report)

    print("Done...")


if __name__ == "__main__":
    main()