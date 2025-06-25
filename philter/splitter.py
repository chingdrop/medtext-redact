import os

import pandas as pd

# Read the CSV file into a pandas dataframe
df = pd.read_csv('C:/Users/luke/Desktop/test/OriginalReports.csv')

# Loop over the rows in the dataframe
for index, row in df.iterrows():
    # Get the values from the 'Accession' and 'Report' columns
    accession = str(row['Accession'])
    report = str(row['Reports'])
    os.chdir("C:/Users/luke/Desktop/test/input")
    print(f"Converting file: {accession}")
    # Create a new text file with the name of the accession and write the report to it
    with open(f'{accession}.txt', 'w') as f:
        f.write(report)

print("Done...")
