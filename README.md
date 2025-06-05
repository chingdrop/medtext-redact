# Vt-Console

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