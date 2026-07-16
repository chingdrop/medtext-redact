# Philter

Vega Imaging Informatics local deployment of Philter-UCSF, read more about the project here: [GitHub - philter-ucsf](https://github.com/BCHSI/philter-ucsf)

Per their instructions, we have a local compilation of the source code as a folder in project.
As far as Git is concerned, philter-ucsf is being treated as sub-module. This allows us to stay connected to their repository and maintain our own version control.

## How to Use

This workflow is run through the `vega-tools` CLI, not as a standalone script — see the root [README](../../README.md#process) for the `philter` command. In short:

1. Create a reference CSV with `Accession` and `Reports` columns.
2. Set up a separate Python environment with `philter-ucsf`'s own dependencies installed (see `philter-ucsf/requirements.txt` — these versions conflict with Vega-Tools' own, so this must not be the same environment `vega-tools` itself runs in).
3. Run `vega-tools philter --sample <path to your CSV> --result <output path> --python <path to that environment's interpreter>` (or set `PHILTER_PYTHON` instead of passing `--python` each time).
4. The de-identified reports are written to the `--result` CSV.
