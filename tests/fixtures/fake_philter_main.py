"""
Stand-in for philter-ucsf/main.py's CLI contract, used only in tests.

The real Philter-UCSF can't run in this environment (it pins pandas/numpy
versions incompatible with vega-tools' own, and imports the long-removed
distutils module), so this fakes just enough of its interface — accept the
same flags commands/philter.py passes, and copy input .txt files to the
output directory — to exercise the split -> subprocess -> repackage wiring
end-to-end without needing the real tool installed.
"""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-f", "--filters", required=True)
    parser.add_argument("--prod")
    parser.add_argument("--outputformat")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    for txt_file in input_dir.glob("*.txt"):
        shutil.copy(txt_file, output_dir / txt_file.name)


if __name__ == "__main__":
    main()
