#!/bin/bash
set -e

if [ ! -z "$JSL_VERSION" ]; then
    echo "Installing spark-nlp-jsl==$JSL_VERSION..."
    pip3 install --no-cache-dir spark-nlp-jsl==$JSL_VERSION \
        --extra-index-url https://pypi.johnsnowlabs.com/$SECRET
fi

if [ ! -z "$OCR_VERSION" ]; then
    echo "Installing spark-ocr==$OCR_VERSION..."
    pip3 install --no-cache-dir spark-ocr==$OCR_VERSION \
        --extra-index-url https://pypi.johnsnowlabs.com/$SPARK_OCR_SECRET
fi

echo "Installing spark-nlp-display..."
pip3 install --no-cache-dir spark-nlp-display

# Exec the command passed via CMD (e.g., Jupyter Notebook)
exec "$@"
