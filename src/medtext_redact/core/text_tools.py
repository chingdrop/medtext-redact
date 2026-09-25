import re
from re import Pattern

import pandas as pd
from rich.console import Console
from rich.text import Text
from shared_tools.config_loader import ConfigLoader

from medtext_redact.core.utils.enums import load_census_names
from medtext_redact.core.utils.regex_utils import (
    NameMasker,
    compile_keywords_pattern,
    mask_keywords,
    mask_regex_pattern,
)

#   USPS street-suffix vocabulary (the standard "C1 Street Suffix
#   Abbreviations" list), used to recognize a street address without any
#   NLP: <house number> <1-4 words> <suffix>. Heuristic, not exhaustive --
#   addresses have no fixed format -- but covers the standard suffixes and
#   the (sometimes fanciful) ones common test-data generators produce.
#   Deliberately excludes a handful of official USPS suffixes that double
#   as ordinary English words much more likely to appear in clinical prose
#   than in an actual street name: "Via" ("treated via telehealth"),
#   "Bend"/"Beach"/"Bluff"/"Bottom" (anatomical/descriptive usage), "Annex"/
#   "Arcade"/"Bayoo" (rare enough not to be worth the risk either way).
_STREET_SUFFIXES = [
    "Alley",
    "Avenue",
    "Ave",
    "Boulevard",
    "Branch",
    "Bridge",
    "Brook",
    "Brooks",
    "Burg",
    "Burgs",
    "Bypass",
    "Camp",
    "Canyon",
    "Cape",
    "Causeway",
    "Center",
    "Centers",
    "Circle",
    "Circles",
    "Cliff",
    "Cliffs",
    "Club",
    "Common",
    "Commons",
    "Corner",
    "Corners",
    "Course",
    "Court",
    "Courts",
    "Cove",
    "Coves",
    "Creek",
    "Crescent",
    "Crest",
    "Crossing",
    "Crossroad",
    "Crossroads",
    "Curve",
    "Dale",
    "Dam",
    "Divide",
    "Drive",
    "Drives",
    "Estate",
    "Estates",
    "Expressway",
    "Extension",
    "Extensions",
    "Fall",
    "Falls",
    "Ferry",
    "Field",
    "Fields",
    "Flat",
    "Flats",
    "Ford",
    "Fords",
    "Forest",
    "Forge",
    "Forges",
    "Fork",
    "Forks",
    "Fort",
    "Freeway",
    "Garden",
    "Gardens",
    "Gateway",
    "Glen",
    "Glens",
    "Green",
    "Greens",
    "Grove",
    "Groves",
    "Harbor",
    "Harbors",
    "Haven",
    "Heights",
    "Highway",
    "Hill",
    "Hills",
    "Hollow",
    "Inlet",
    "Island",
    "Islands",
    "Isle",
    "Junction",
    "Junctions",
    "Key",
    "Keys",
    "Knoll",
    "Knolls",
    "Lake",
    "Lakes",
    "Land",
    "Landing",
    "Lane",
    "Light",
    "Lights",
    "Loaf",
    "Lock",
    "Locks",
    "Lodge",
    "Loop",
    "Mall",
    "Manor",
    "Manors",
    "Meadow",
    "Meadows",
    "Mews",
    "Mill",
    "Mills",
    "Mission",
    "Motorway",
    "Mount",
    "Mountain",
    "Mountains",
    "Neck",
    "Orchard",
    "Oval",
    "Overpass",
    "Park",
    "Parks",
    "Parkway",
    "Parkways",
    "Pass",
    "Passage",
    "Path",
    "Pike",
    "Pine",
    "Pines",
    "Place",
    "Plain",
    "Plains",
    "Plaza",
    "Point",
    "Points",
    "Port",
    "Ports",
    "Prairie",
    "Radial",
    "Ramp",
    "Ranch",
    "Rapid",
    "Rapids",
    "Rest",
    "Ridge",
    "Ridges",
    "River",
    "Road",
    "Roads",
    "Route",
    "Row",
    "Rue",
    "Run",
    "Shoal",
    "Shoals",
    "Shore",
    "Shores",
    "Skyway",
    "Spring",
    "Springs",
    "Spur",
    "Spurs",
    "Square",
    "Squares",
    "Station",
    "Stravenue",
    "Stream",
    "Street",
    "Streets",
    "Summit",
    "Terrace",
    "Throughway",
    "Trace",
    "Track",
    "Trafficway",
    "Trail",
    "Tunnel",
    "Turnpike",
    "Underpass",
    "Union",
    "Unions",
    "Valley",
    "Valleys",
    "Viaduct",
    "View",
    "Views",
    "Village",
    "Villages",
    "Ville",
    "Vista",
    "Walk",
    "Walks",
    "Wall",
    "Way",
    "Ways",
    "Well",
    "Wells",
    "Blvd",
    "Dr",
    "Rd",
    "Ln",
    "Ct",
    "Pl",
    "Ter",
    "Cir",
    "Hwy",
    "Pkwy",
    "Sq",
    "Trl",
    "Rte",
    "St",
]


class PhiSanitizer:
    """
    Phi Sanitizer de-identifies sensitive information using regex patterns and a custom regex replacer.

    Args:
        text (str): The report text.
    """

    # ‣ Allow `/`, `-` or `.` as separators (and require you use the same one each time)
    # ‣ Constrain years to 1900–2099
    # ‣ Word‐boundaries so you don’t accidentally pick up “20212” or “13/40/1990”
    _DATE_PATTERN = re.compile(
        r"""\b
            (?:0?[1-9]|1[0-2])           # month 1–9 or 01–09 or 10–12
            (?P<sep>[/\-.])              # separator: slash, dash, or dot
            (?:0?[1-9]|[12][0-9]|3[01])  # day 1–9, 01–09, 10–29, 30, 31
            (?P=sep)                     # same sep as before
            (?:19|20)\d{2}               # year 1900–2099
            \b
            """,
        re.VERBOSE,
    )

    # ‣ Optional country code, area code (parens optional), exchange, line
    # ‣ (?<!\d) / (?!\d) instead of \b so a leading "(" doesn't swallow the boundary
    _PHONE_PATTERN = re.compile(
        r"""(?<!\d)
            (?:\+?1[\s.\-]?)?
            \(?\d{3}\)?[\s.\-]?
            \d{3}[\s.\-]?\d{4}
            (?!\d)
            """,
        re.VERBOSE,
    )

    # ‣ Requires the literal "MRN" label -- an unlabeled digit run is too
    #   ambiguous with any other number to safely treat as a record number
    _MRN_PATTERN = re.compile(
        r"""\bMRN
            [\s:\-]*
            [A-Za-z]{0,3}-?
            \d{5,10}
            \b
            """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ‣ <house number> <0-4 words> <USPS street suffix>, optionally + Apt/Suite/Unit
    # ‣ Heuristic, not exhaustive -- addresses have no single fixed format
    _ADDRESS_PATTERN = re.compile(
        r"""\b\d{1,6}\s+
            (?:[A-Za-z0-9'.]+\s+){0,4}
            (?:"""
        + "|".join(sorted(set(_STREET_SUFFIXES), key=len, reverse=True))
        + r""")\.?
            (?:\s+(?:Apt\.?|Suite|Ste\.?|Unit|\#)\s*[A-Za-z0-9\-]+)?
            \b
            """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ‣ Restrict age to 0–150
    # ‣ Allow "34", "34 yrs", "34-yrs-old", "34 years old", "34yo", case‐insensitive
    # ‣ Don't treat a clinical staging/grading number ("type 2 diabetes",
    #   "stage 3 cancer") as an age -- a real cross-feature bug an E2E test
    #   surfaced: that digit getting masked broke --keywords search/highlight
    #   for the very diagnosis term it was part of.
    _AGE_PATTERN = re.compile(
        r"""(?<!type\s)(?<!stage\s)(?<!grade\s)(?<!class\s)
            \b
            (?:                           # whole age number
               0|[1-9][0-9]?|1[0-4][0-9]|150
            )
            (?:                           # optional unit + “old”
              [\s\-]*                     # space or hyphen
              (?:years?|yrs?|yo|y|yr)     # year(s) variants, incl. "yo" shorthand
            )?
            (?:[\s\-]*old)?               # optional “old”
            \b
            """,
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(self, text: str | None, title_case: bool = False) -> None:
        self.title_case = title_case
        self._text = "" if pd.isna(text) else text.strip()
        self._format_text()

    def _format_text(self) -> None:
        text = re.sub(r"\s+", " ", self._text)
        text = re.sub(r"\s*,\s*", ", ", text)
        if self.title_case:
            # Only uppercase first letter of sentence, if needed, rather than each word
            text = ". ".join(s.capitalize() for s in text.split(". "))
        self._text = text.strip()

    @property
    def text(self) -> str:
        return self._text

    def sanitize_keywords(self, keywords: list[str]) -> "PhiSanitizer":
        """Mask out any occurrences of the provided keywords."""
        self._text = mask_keywords(self._text, keywords)
        return self

    def sanitize_names(self) -> "PhiSanitizer":
        """Load census names and mask any occurrences."""
        names = load_census_names()
        nm = NameMasker(names)
        self._text = nm.mask(self._text)
        return self

    def sanitize_dates(self) -> "PhiSanitizer":
        """Mask all dates matching MM/DD/YYYY or M/D/YYYY."""
        self._text = mask_regex_pattern(self._DATE_PATTERN, self._text)
        return self

    def sanitize_mrn(self) -> "PhiSanitizer":
        """Mask medical record numbers labeled with 'MRN' (e.g. 'MRN-1234567')."""
        self._text = mask_regex_pattern(self._MRN_PATTERN, self._text)
        return self

    def sanitize_phone(self) -> "PhiSanitizer":
        """Mask US phone numbers in common formats."""
        self._text = mask_regex_pattern(self._PHONE_PATTERN, self._text)
        return self

    def sanitize_address(self) -> "PhiSanitizer":
        """Mask street addresses (house number + street name + USPS suffix)."""
        self._text = mask_regex_pattern(self._ADDRESS_PATTERN, self._text)
        return self

    def sanitize_age(self) -> "PhiSanitizer":
        """Mask age expressions like '34 years old' or '100-yrs-old'."""
        self._text = mask_regex_pattern(self._AGE_PATTERN, self._text)
        return self

    def sanitize_gender(self) -> "PhiSanitizer":
        """Mask simple gender terms."""
        return self.sanitize_keywords(["male", "female", "males", "females"])

    def sanitize_all(self, config: ConfigLoader, full: bool = False) -> "PhiSanitizer":
        """
        De‐identify PHI using the provided ConfigLoader.

        Args:
            config: a ConfigLoader instance whose config contains
                    a 'Masking' section with 'Manufacturers' and 'Locations'.
            full: if True, also mask gender + age
        """
        # MRN before phone: a labeled MRN ("MRN 1234567890") is otherwise
        # digit-shaped enough to also match the phone pattern -- masking it
        # first removes the ambiguity rather than relying on match order
        # inside a single pass.
        self.sanitize_names().sanitize_mrn().sanitize_phone().sanitize_address().sanitize_dates()
        if full:
            self.sanitize_gender().sanitize_age()

        manufacturers = config.get("Masking.Manufacturers")
        locations = config.get("Masking.Locations")

        if manufacturers:
            self.sanitize_keywords(manufacturers)
        if locations:
            self.sanitize_keywords(locations)

        return self


def _highlight_text(text: str, pattern: Pattern[str], style: str = "bold yellow") -> Text:
    """
    Return a Rich Text object with every regex match styled.
    """
    t = Text(text)
    for m in pattern.finditer(text):
        t.stylize(style, m.start(), m.end())
    return t


def print_lines_with_keywords(
    keywords: list[str],
    text: str,
    *,
    boundary: bool = True,
    style: str = "bold yellow",
    console: Console | None = None,
) -> None:
    """
    Split `text` into sentences (on .?!), find lines containing any keyword,
    and print each line with the keywords highlighted.
    """
    console = console or Console()
    pattern = compile_keywords_pattern(keywords, boundary=boundary)

    sentences = re.split(r"(?<=[.?!])\s+", text)
    for sentence in sentences:
        if pattern.search(sentence):
            highlighted = _highlight_text(sentence.strip(), pattern, style)
            console.print(highlighted)


def print_text_with_keywords(
    keywords: list[str], text: str, *, boundary: bool = True, style: str = "bold yellow"
) -> None:
    """Highlight all occurrences of `keywords` in the full `text` and page it via the system pager (using PyDoc)."""
    import pydoc
    from io import StringIO

    pattern = compile_keywords_pattern(keywords, boundary=boundary)
    highlighted = _highlight_text(text, pattern, style)

    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True)
    console.print(highlighted)
    pydoc.pager(buffer.getvalue())


# ---- Client Specific Functions ---- #
def white_rabbit_parse_report(text: str) -> str:
    """
    Sanitize Penrad Doctor signature with custom masking.

    Args:
        text (str): The report text.

    Returns:
        str: The report text with Penrad masked.
    """
    penrad_pattern = r"[a-zA-Z]{2,3}/Penrad"
    return mask_regex_pattern(penrad_pattern, text)
