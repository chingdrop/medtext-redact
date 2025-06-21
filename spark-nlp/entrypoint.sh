#!/usr/bin/env bash
set -euo pipefail

# If you want to pin spark-ocr or spark-nlp-jsl to a version different
# from PUBLIC_VERSION, define OCR_VERSION or JSL_VERSION in your .env.
# Otherwise they default to PUBLIC_VERSION.
OCR_VER=${OCR_VERSION:-$PUBLIC_VERSION}
JSL_VER=${JSL_VERSION:-$PUBLIC_VERSION}

echo "Installing spark-ocr==${OCR_VER} from private index"
pip install --upgrade -q spark-ocr==${OCR_VER} \
    --extra-index-url=https://pypi.johnsnowlabs.com/${SPARK_OCR_LICENSE}

echo "Installing pyspark==3.4.0 and spark-nlp==${PUBLIC_VERSION}"
pip install --upgrade -q pyspark==3.4.0 spark-nlp==${PUBLIC_VERSION}

echo "Installing spark-nlp-jsl==${JSL_VER} from private index"
pip install --upgrade -q spark-nlp-jsl==${JSL_VER} \
    --extra-index-url=https://pypi.johnsnowlabs.com/${SPARK_NLP_LICENSE}"

# Finally, launch Jupyter (or whatever your CMD is)
exec jupyter notebook \
  --port=8888 \
  --no-browser \
  --ip=0.0.0.0 \
  --NotebookApp.token='' \
  --NotebookApp.password='' \
  --allow-root
