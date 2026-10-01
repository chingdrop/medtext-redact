import tldextract.tldextract

from medtext_redact.core.presidio_tools import presidio_redact


class TestPresidioRedact:
    def test_masks_names_outside_any_gazetteer(self):
        result = presidio_redact("Dr. Novak examined Elena this morning.")
        assert "Novak" not in result
        assert "Elena" not in result

    def test_masks_email_address(self):
        result = presidio_redact("Contact elena.novak@example.com for records.")
        assert "elena.novak@example.com" not in result

    def test_masks_word_characters_only_preserving_length(self):
        text = "Patient Elena Novak, DOB 5/6/1950, reports chest pain."
        result = presidio_redact(text)
        assert len(result) == len(text)
        assert "DOB */*/****," in result

    def test_leaves_clinical_terms_intact(self):
        text = "Elena Novak was started on metformin for type 2 diabetes mellitus."
        result = presidio_redact(text)
        assert "metformin" in result
        assert "type 2 diabetes mellitus" in result

    def test_text_without_phi_is_unchanged(self):
        text = "Routine follow-up visit. Continue management for hypertension."
        assert presidio_redact(text) == text

    def test_domain_lookups_never_fetch_the_public_suffix_list(self, monkeypatch):
        def no_network(*args, **kwargs):
            raise AssertionError("tldextract tried to fetch the Public Suffix List")

        monkeypatch.setattr(tldextract.suffix_list, "find_first_response", no_network)
        result = presidio_redact("Contact elena.novak@example.com for records.")
        assert "elena.novak@example.com" not in result
        assert tldextract.tldextract.TLD_EXTRACTOR.suffix_list_urls == ()
