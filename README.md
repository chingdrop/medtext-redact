# Vega-Tools

A Command-Line Interface for HIPAA Redaction and Semantic Highlighting in Medical Text

---

## Scope

Vega-Tools is a Python-based command-line utility developed to assist with the secure preprocessing of unstructured medical text. Its primary aim is to enable the automated redaction of Protected Health Information (PHI) in compliance with HIPAA, and the semantic highlighting of domain-relevant keywords to support clinical review and downstream text analytics.

This tool is intended for use by health data engineers, clinical researchers, and compliance teams handling sensitive textual data such as physician notes, diagnostic summaries, and patient-reported outcomes.

---

## Process

Vega-Tools is implemented as a modular CLI using the Click framework and currently supports the following core commands:

- **`redact`**: Applies rule-based and pattern-matching techniques (e.g., regex, named entity recognition) to identify and redact personally identifiable information, including names, dates, addresses, phone numbers, and other HIPAA-defined identifiers.
- **`highlight`**: Scans medical text for pre-defined clinical or operational keywords (e.g., symptom terms, diagnosis codes, drug names), applying color-coded or markup-based emphasis for improved readability and interpretation.

Both commands are accessible via a simple and extensible CLI interface designed for integration into larger preprocessing pipelines or standalone usage by analysts.

In addition to text redaction and highlighting, Vega-Tools includes commands for reconciling imaging studies across projects:

- **`compare-projects`**: Given a spreadsheet of paired studies (`file_1`/`file_2` plus their accession numbers), produces a normalized comparison ordered by project name.
- **`validate-studies`**: Cross-references a project's reference spreadsheet against a sample spreadsheet to confirm each study's accession number appears where expected, flagging failures and prior/index study type.
- **`audit-series-by-study`**: Summarizes which required 2D/3D image series are present or missing per study accession.

Vega-Tools also wraps the GPU-based Spark NLP / Spark OCR de-identification environment in [`spark-nlp/`](spark-nlp/):

- **`spark-nlp`**: Passes arguments straight through to `docker compose`, run from the `spark-nlp/` directory (e.g. `vega-tools spark-nlp down`, `vega-tools spark-nlp logs -f`). With no arguments, it defaults to `up --build`, launching the Jupyter notebook environment. Requires Docker and a `spark-nlp/.env` file with the John Snow Labs license keys (see `spark-nlp/docker-compose.yaml`).