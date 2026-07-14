# Vega-Philter

Vega Imaging Informatics local deployment of Philter-UCSF, read more about the project here: [GitHub - philter-ucsf](https://github.com/BCHSI/philter-ucsf)

Per their instructions, we have a local compilation of the source code as a folder in project. 
As far as Git is concerned, philter-ucsf is being treated as sub-module. This allows us to stay connected to their repository and maintain our own version control.

## How to Use

1. Create a reference CSV file named 'original_reports.csv', that has two columns: 'Accession' and 'Reports'. Accession will hold the accession numbers and Reports will hold the report text.
2. Open File Explorer and navigate to 'C:\Users\luke\Code\vega-philter'.
3. Place your original reports CSV in the 'data' folder.
   - **NEW DEPLOYMENTS ONLY**, create a folder called 'data' and place your original reports CSV there.
4. Open a new PowerShell window and run this line of code: `C:\Users\luke\anaconda3\envs\vega-philter\python.exe C:\Users\luke\Code\vega-philter\main.py`
   - This will run the program from the project's virtual environment.
   - If there are any errors, then please reach out to Vega's Internal IT for support.
5. A file called 'result_report.csv' will be written to the data folder.
