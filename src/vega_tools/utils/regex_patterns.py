import re
from re import Pattern
from typing import List

# ToDo - Add docstrings to better describe Regex operations.
def create_keywords_pattern(keywords: List[str]) -> Pattern:
    # noinspection RegExpUnnecessaryNonCapturingGroup
    return re.compile(fr'\b(?:{"|".join(map(re.escape, keywords))})', re.IGNORECASE)