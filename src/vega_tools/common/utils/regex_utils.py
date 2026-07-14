import re
from typing import List, Union, Pattern, Match


def compile_keywords_pattern(
        keywords: List[str],
        *,
        boundary: bool = True,
        flags: int = re.IGNORECASE
) -> Pattern[str]:
    """
    Build a regex that matches any of the given keywords.

    Args:
        keywords: list of literal strings to match.
        boundary: if True, wrap each in `(?<!\w)...(?!\w)` to force whole-word matches.
        flags: regex flags to compile with (e.g. IGNORECASE).

    Returns:
        A compiled Pattern.

    Raises:
        ValueError  – if keywords is empty.
        TypeError   – if any keyword is not a str.
    """
    if not keywords:
        raise ValueError("`keywords` must contain at least one entry")
    if not all(isinstance(k, str) for k in keywords):
        raise TypeError("All keywords must be str")

    # Sort by length descending so longer ones get matched first (“Washington” before “Wash”)
    unique = sorted(set(keywords), key=len, reverse=True)
    escaped = [re.escape(k) for k in unique]
    group = "|".join(escaped)

    if boundary:
        # (?<!\w) and (?!\w) are more robust than \b when keywords contain underscores, etc.
        pattern = rf"(?<!\w)(?:{group})(?!\w)"
    else:
        pattern = rf"(?:{group})"

    return re.compile(pattern, flags)


def mask_regex_pattern(
        pattern: Union[str, Pattern[str]],
        text: str,
        *,
        mask_char: str = '*',
        char_class: str = r'\w'
) -> str:
    """
    Mask all matches of `pattern` in `text`, replacing each alphanumeric
    character with `mask_char` (default '*').

    Args:
        pattern: a compiled Pattern or a regex string.
        text: the input to mask.
        mask_char: the single-character string to replace each matched char with.
        char_class: a character class (e.g. '\\w', '[A-Za-z0-9]')
                    specifying which characters inside the match to mask.

    Returns:
        The masked string.
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)

    def repl(m: Match[str]) -> str:
        s = m.group(0)
        # Only mask characters matching `char_class`; leave punctuation/spaces
        return ''.join(
            mask_char if re.fullmatch(char_class, c) else c
            for c in s
        )

    return pattern.sub(repl, text)


def mask_keywords(
        text: str,
        keywords: List[str],
        *,
        boundary: bool = True,
        mask_char: str = '*'
) -> str:
    """
    Shortcut for masking a list of keywords in `text`.

    Args:
        text:       the input string.
        keywords:   list of words/phrases to mask.
        boundary:   whether to force whole-word matches.
        mask_char:  character to use for masking.

    Returns:
        The masked string.
    """
    pat = compile_keywords_pattern(keywords, boundary=boundary)
    return mask_regex_pattern(pat, text, mask_char=mask_char)


class NameMasker:
    """
    Uses Aho-Corasick to create a dictionary of patterns and repls to optimize masking for large datasets.

    Args:
        names (List[str]): List of names.

    Attributes:
        automaton (Automation): Aho-Corasick automaton object.
    """

    def __init__(self, names: List[str]):
        import ahocorasick

        self.automaton = ahocorasick.Automaton()
        for name in names:
            self.automaton.add_word(name, "*" * len(name))
        self.automaton.make_automaton()

    def mask(self, text: str) -> str:
        """
        Walk the text once, replacing any matched key with its associated mask.

        Args:
            text (str): The text to mask.

        Returns:
            str: The masked text.
        """
        result = []
        last_idx = 0

        for end_idx, mask in self.automaton.iter(text):
            start_idx = end_idx - len(mask) + 1
            result.append(text[last_idx:start_idx])
            result.append(mask)
            last_idx = end_idx + 1

        result.append(text[last_idx:])
        return ''.join(result)
