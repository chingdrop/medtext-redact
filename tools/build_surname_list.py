#!/usr/bin/env python3
"""
Build the bundled US Census 2010 surname list used by the PERSON gazetteer.

Writes src/medtext_redact/data/census_2010_surnames.txt: every surname
reported 100 or more times in the 2010 Census, title-cased, one per line,
in national rank order. Census Bureau data is a work of the US government
and in the public domain.

Two sources for the same dataset:

    # The "names.zip" archive, downloaded in a browser from
    # https://www2.census.gov/topics/genealogy/2010surnames/names.zip
    uv run python tools/build_surname_list.py --zip ~/Downloads/names.zip

    # The Census Data API (free key: https://api.census.gov/data/key_signup.html)
    CENSUS_API_KEY=... uv run python tools/build_surname_list.py --api
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "src" / "medtext_redact" / "data" / "census_2010_surnames.txt"
API_URL = "https://api.census.gov/data/2010/surname"

# Both sources include an aggregate row for every surname below the
# 100-occurrence cutoff. It isn't a surname.
_AGGREGATE_ROW = "ALL OTHER NAMES"

# The 2010 release lists 162,253 surnames; a much smaller result means a
# truncated download or the wrong file, not a smaller dataset.
_MIN_EXPECTED = 150_000


def surnames_from_zip(path: Path) -> list[str]:
    """Read the `name` column of the CSV inside the census names.zip, in rank order."""
    with zipfile.ZipFile(path) as archive:
        (csv_name,) = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        with archive.open(csv_name) as raw:
            rows = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            return [row["name"] for row in rows]


def surnames_from_api(key: str) -> list[str]:
    """Fetch every surname from the Census Data API, in rank order."""
    query = urllib.parse.urlencode({"get": "NAME,RANK", "RANK": "1:999999", "key": key})
    with urllib.request.urlopen(f"{API_URL}?{query}", timeout=120) as response:  # noqa: S310 - constant https endpoint
        body = response.read()
    try:
        header, *rows = json.loads(body)
    except json.JSONDecodeError as exc:
        # An invalid key gets an HTML page rather than JSON.
        raise SystemExit(f"The Census API didn't return JSON (is the key valid?): {body[:200]!r}") from exc
    name_col, rank_col = header.index("NAME"), header.index("RANK")
    rows.sort(key=lambda row: int(row[rank_col]))
    return [row[name_col] for row in rows]


def normalize(names: list[str]) -> list[str]:
    """Title-case each surname, dropping blanks, the aggregate row, and repeats."""
    seen: set[str] = set()
    result = []
    for name in names:
        name = name.strip()
        if not name or name.upper() == _AGGREGATE_ROW:
            continue
        titled = name.title()
        if titled not in seen:
            seen.add(titled)
            result.append(titled)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--zip", type=Path, help="Path to a downloaded names.zip")
    source.add_argument("--api", action="store_true", help="Fetch from the Census Data API (needs CENSUS_API_KEY)")
    parser.add_argument("--out", type=Path, default=OUTPUT, help=f"Output file (default: {OUTPUT})")
    args = parser.parse_args()

    if args.api:
        key = os.environ.get("CENSUS_API_KEY")
        if not key:
            sys.exit("Set CENSUS_API_KEY (free key: https://api.census.gov/data/key_signup.html)")
        names = normalize(surnames_from_api(key))
    else:
        names = normalize(surnames_from_zip(args.zip))

    if len(names) < _MIN_EXPECTED:
        sys.exit(f"Only {len(names):,} surnames found; expected about 162,000. Not writing {args.out}.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"Wrote {len(names):,} surnames to {args.out}")


if __name__ == "__main__":
    main()
