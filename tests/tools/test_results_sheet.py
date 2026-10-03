import importlib.util
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
_spec = importlib.util.spec_from_file_location("results_sheet", TOOLS_DIR / "results_sheet.py")
sheet = importlib.util.module_from_spec(_spec)
sys.modules["results_sheet"] = sheet
_spec.loader.exec_module(sheet)


def result(tp=0, fn=0, fp=0, tn=0):
    recall = tp / (tp + fn) if tp + fn else None
    precision = tp / (tp + fp) if tp + fp else None
    return {"recall": recall, "precision": precision, "tp": tp, "fn": fn, "fp": fp, "tn": tn}


def span(category, start, end, text, *, expected=True, hit=True):
    return {"category": category, "start": start, "end": end, "text": text, "expected_redacted": expected, "hit": hit}


def make_data(**overrides):
    text = "Patient Smith <x> has fever."
    data = {
        "seed": 7,
        "note_count": 2,
        "template_count": 1,
        "results": {
            "name": result(tp=3, fn=1),
            "email": result(tp=2),
            "highlight_symptom": result(tp=4),
            "name_common_word": result(fp=1, tn=3),
        },
        "notes": [
            {
                "template_index": 0,
                "text": text,
                "rendered": "******* ***** <x> has fever.",
                "spans": [span("name", 8, 13, "Smith"), span("highlight_symptom", 22, 27, "fever")],
            }
        ],
    }
    data.update(overrides)
    return data


class TestBuild:
    def test_headline_numbers_come_from_the_results(self):
        page = sheet.build(make_data())
        assert "5<small> / 6</small>" in page  # identifiers masked: name 3/4 + email 2/2
        assert "1<small> / 2</small>" in page  # categories at 100% recall: email only
        assert "4<small> / 4</small>" in page  # clinical terms kept
        assert "1<small> / 4</small>" in page  # decoys masked

    def test_note_text_is_html_escaped(self):
        page = sheet.build(make_data())
        assert "&lt;x&gt;" in page
        assert "<x>" not in page

    def test_masking_outside_labeled_spans_is_marked(self):
        # "Patient" is masked in the rendering but isn't a labeled identifier.
        page = sheet.build(make_data())
        assert "<span class='over'>*******</span>" in page

    def test_unknown_categories_still_appear(self):
        data = make_data()
        data["results"]["new_detector"] = result(tp=1)
        assert "new_detector" in sheet.build(data)

    def test_a_category_below_full_recall_is_flagged(self):
        page = sheet.build(make_data())
        assert "fill short" in page  # name: 3 of 4
