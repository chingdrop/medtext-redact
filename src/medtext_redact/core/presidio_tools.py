import re
from functools import lru_cache

import tldextract.tldextract
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

SPACY_MODEL = "en_core_web_lg"

_WORD_CHAR = re.compile(r"\w")


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    """Build the analyzer once per process -- loading the spaCy model takes seconds."""
    # Presidio's email recognizer calls tldextract.extract(), whose shared
    # default extractor downloads the Public Suffix List on first use. Swap
    # in one that only reads tldextract's bundled snapshot, so the census
    # surname download stays this tool's only network call.
    tldextract.tldextract.TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())
    provider = NlpEngineProvider(
        nlp_configuration={"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": SPACY_MODEL}]}
    )
    return AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])


def presidio_redact(text: str) -> str:
    """Mask every entity Presidio's default English recognizers detect in `text`."""
    # Same masking style as mask_regex_pattern(): every word character in a
    # detected span becomes "*", punctuation and length are preserved, so
    # keyword highlighting and the recall/precision suite's span offsets
    # stay aligned. Masking is idempotent, so overlapping spans need no
    # merging -- which is all presidio-anonymizer would add here.
    chars = list(text)
    for result in _analyzer().analyze(text=text, language="en"):
        for i in range(result.start, result.end):
            if _WORD_CHAR.match(chars[i]):
                chars[i] = "*"
    return "".join(chars)
