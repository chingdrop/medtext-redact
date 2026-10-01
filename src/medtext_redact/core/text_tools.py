import re
from re import Pattern

import pandas as pd
from rich.console import Console
from rich.text import Text

from medtext_redact.core.utils.enums import load_census_names
from medtext_redact.core.utils.regex_utils import (
    compile_keywords_pattern,
    mask_keywords,
    mask_regex_pattern,
)
from medtext_redact.vendor.config_loader import ConfigLoader


class PhiSanitizer:
    """
    Normalizes a report's whitespace, then de-identifies it: Presidio for PHI
    detection, plus any keyword masks from the client config.

    Args:
        text (str): The report text.
    """

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

    def sanitize_configured_keywords(self, config: ConfigLoader) -> "PhiSanitizer":
        """Mask the config's 'Masking.Manufacturers' and 'Masking.Locations' keyword lists."""
        manufacturers = config.get("Masking.Manufacturers")
        locations = config.get("Masking.Locations")

        if manufacturers:
            self.sanitize_keywords(manufacturers)
        if locations:
            self.sanitize_keywords(locations)

        return self

    def sanitize_presidio(self) -> "PhiSanitizer":
        """Mask every entity Microsoft Presidio detects: its NER and built-in recognizers plus the ported rules."""
        # Imported here so commands that never redact don't pay for loading spaCy.
        from medtext_redact.core.presidio_tools import presidio_redact

        self._text = presidio_redact(self._text, load_census_names())
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
