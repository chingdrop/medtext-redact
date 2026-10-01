import re
from functools import lru_cache

import tldextract.tldextract
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

SPACY_MODEL = "en_core_web_lg"

#   Same masking style as mask_regex_pattern(): every word character becomes
#   "*", punctuation and length are preserved. Keeping the text the same
#   length keeps keyword highlighting and the recall/precision suite's span
#   offsets aligned regardless of which engine produced the redaction.
_MASK_OPERATOR = OperatorConfig("custom", {"lambda": lambda s: re.sub(r"\w", "*", s)})


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


@lru_cache(maxsize=1)
def _anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()


def presidio_redact(text: str) -> str:
    """Mask every entity Presidio's default English recognizers detect in `text`."""
    # The anonymizer declares its own RecognizerResult type rather than
    # importing the analyzer's, so convert explicitly between the two.
    results = [
        RecognizerResult(r.entity_type, r.start, r.end, r.score) for r in _analyzer().analyze(text=text, language="en")
    ]
    return _anonymizer().anonymize(text=text, analyzer_results=results, operators={"DEFAULT": _MASK_OPERATOR}).text
