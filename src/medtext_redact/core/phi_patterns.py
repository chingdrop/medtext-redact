"""
The regex patterns behind PHI detection, shared by both engines:
PhiSanitizer's own masking and the Presidio recognizers built on them.
"""

import re

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
STREET_SUFFIXES = [
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


# ‣ Allow `/`, `-` or `.` as separators (and require you use the same one each time)
# ‣ Constrain years to 1900–2099
# ‣ Word‐boundaries so you don’t accidentally pick up “20212” or “13/40/1990”
DATE_PATTERN = re.compile(
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
PHONE_PATTERN = re.compile(
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
MRN_PATTERN = re.compile(
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
ADDRESS_PATTERN = re.compile(
    r"""\b\d{1,6}\s+
        (?:[A-Za-z0-9'.]+\s+){0,4}
        (?:"""
    + "|".join(sorted(set(STREET_SUFFIXES), key=len, reverse=True))
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
AGE_PATTERN = re.compile(
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
