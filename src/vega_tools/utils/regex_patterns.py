import re
from re import Pattern
from typing import List


def create_keywords_pattern(keywords: List[str]) -> Pattern:
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