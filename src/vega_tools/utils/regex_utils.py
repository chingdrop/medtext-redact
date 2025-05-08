import re
from re import Pattern, Match
from typing import List


# ToDo - Add parameter to select whether to add word boundaries
def create_keywords_pattern(keywords: List[str]) -> Pattern[str]:
    """
    Create a compiled regular expression pattern to match any of the given keywords.

    Args:
        keywords (list[str]): List of keywords.

    Returns:
        Pattern: A compiled regular expression pattern.

    Raises:
        TypeError: If any of the given keywords is not a string.
    """
    if not all(isinstance(keyword, str) for keyword in keywords):
        raise TypeError('Keywords must be a list of strings')
    # noinspection RegExpUnnecessaryNonCapturingGroup
    return re.compile(fr'\b({"|".join(map(re.escape, keywords))})', re.IGNORECASE)


def mask_regex_pattern(match: Pattern | str, text: str) -> str:
    """
    Use a regex pattern to mask matches in the given text.
    The custom replacer function will mask letters and numbers as asterisks.

    Args:
        match (Pattern | str): A compiled regular expression pattern.
        text (str): The text to mask.

    Returns:
        str: The masked text.
    """
    if isinstance(match, str):
        match = re.compile(match, flags=re.IGNORECASE)

    def custom_repl(value: Match) -> str:
        return re.sub(r'[A-Za-z0-9]', '*', value.group())

    return re.sub(match, custom_repl, text)


def mask_keywords(text: str, keywords: List[str]) -> str:
    """
    Given a list of keywords, create a regular expression pattern and mask the text.

    Args:
        text (str): The text to mask.
        keywords (list[str]): List of keywords.

    Returns:
        str: The masked text.
    """
    keywords_pattern = create_keywords_pattern(keywords)
    return mask_regex_pattern(keywords_pattern, text)
