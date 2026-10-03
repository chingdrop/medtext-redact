from functools import lru_cache
from importlib.resources import files

#   Every surname reported 100+ times in the 2010 US Census (public domain),
#   title-cased, one per line, in national rank order. Built by
#   tools/build_surname_list.py and bundled with the package rather than
#   downloaded at runtime, so redaction makes no network calls -- and isn't
#   at the mercy of census.gov's firewall, which rejects automated downloads
#   from some networks.
SURNAMES_RESOURCE = files("medtext_redact.data") / "census_2010_surnames.txt"


@lru_cache(maxsize=1)
def load_census_names() -> tuple[str, ...]:
    """The bundled census surname list, read once per process."""
    try:
        text = SURNAMES_RESOURCE.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"The bundled census surname list is missing ({SURNAMES_RESOURCE}). "
            "Rebuild it with tools/build_surname_list.py."
        ) from exc
    return tuple(line for line in text.splitlines() if line)


DICOM_2D_SERIES_DESCRIPTIONS = {"V-Preview RCC", "V-Preview LCC", "V-Preview LMLO", "V-Preview RMLO"}
DICOM_3D_SERIES_DESCRIPTIONS = {"ROUTINE3D_VOL_RCC", "ROUTINE3D_VOL_LCC", "ROUTINE3D_VOL_LMLO", "ROUTINE3D_VOL_RMLO"}
