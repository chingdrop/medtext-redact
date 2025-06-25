import os

import pandas as pd

# specify the directory containing the .txt files
directory = 'C:/Users/luke/Desktop/test/output'

# initialize an empty list to store the data
data = []

# loop through all the .txt files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        # read the contents of the file
        with open(os.path.join(directory, filename), 'r') as f:
            contents = f.read()

        # append the filename and contents to the list
        data.append((filename, contents))

# create a Pandas dataframe from the list
df = pd.DataFrame(data, columns=['Filename', 'Contents'])

# save the dataframe to a CSV file
df.to_csv('C:/Users/luke/Desktop/test/DEID_Reports.csv', index=False)
