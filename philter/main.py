#Import key operating system functionality
import os
import nltk

#Set up base directories which contain the input reports (as individual .txt files) and output directory (this can contain
# either .txt or .xml files, depending on which PHILTER command line script is run)
baseDir = f"C:/Users/luke/Desktop/test"
txtInputDir = "C:/Users/luke/Desktop/test/input/"
outputDir = "C:/Users/luke/Desktop/test/output/"
#This is the default path to a configurations file required for PHILTER to run. It should use the default but I ran into issues unless the location is hardcoded
philterDeltaPath = ('C:/Users/luke/PycharmProjects/pythonProject/philter-ucsf/configs/philter_delta.js'
                    ''
                    ''
                    '\
                    on')
#This is simply the home folder of the PHILTER repository which we copied via github
philterBaseDir = 'C:/Users/luke/PycharmProjects/pythonProject/philter-ucsf/'


#Change to home directory of the cloned PHILTER repository to run the command from.
os.chdir(philterBaseDir)
# os.system(f'python main.py -i {txtInputDir} -o {outputDir} -f {philterDeltaPath} --prod=True --v=False') #XML FORMAT
os.system(f'python main.py -i {txtInputDir} -o {outputDir} -f {philterDeltaPath} --prod=True --outputformat "asterisk"') #Asterisked Format



print("Done...")
