#!/bin/bash
if [ ! -z "$JSL_VERSION" ]; then
    echo "Installing spark-nlp-jsl packages..."
    pip install --upgrade spark-nlp-jsl==$JSL_VERSION --user --extra-index-url https://pypi.johnsnowlabs.com/$SECRET
fi
if [ ! -z "$OCR_VERSION" ]; then
    echo "Installing spark-ocr packages..."
    pip install --upgrade spark-ocr==$OCR_VERSION --user --extra-index-url https://pypi.johnsnowlabs.com/$SPARK_OCR_SECRET
fi

if [ $? != 0 ];
then
    exit 1
fi

pip install --upgrade spark-nlp-display

jupyter notebook --port=8888 --no-browser --ip=0.0.0.0 --NotebookApp.token='' --NotebookApp.password='' --allow-root
