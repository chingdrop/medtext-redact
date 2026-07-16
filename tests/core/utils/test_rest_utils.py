from unittest.mock import MagicMock

import pytest
import requests

from vega_tools.core.utils.rest_utils import RestAdapter, RestAdapterConfig


class TestRestAdapterConfig:
    def test_defaults(self):
        config = RestAdapterConfig(base_url="https://example.com")
        assert config.headers == {}
        assert config.auth is None
        assert config.proxies == {}
        assert config.timeout is None
        assert config.verify is True
        assert config.retries == 3
        assert config.backoff_factor == 0.3

    def test_default_mutable_fields_are_independent_between_instances(self):
        a = RestAdapterConfig(base_url="https://a.com")
        b = RestAdapterConfig(base_url="https://b.com")
        a.headers["X"] = "1"
        assert b.headers == {}


def make_response(*, status_code=200, json_data=None, text=None, content=None, content_type="application/json"):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    if json_data is not None:
        resp.json.return_value = json_data
    if text is not None:
        resp.text = text
    if content is not None:
        resp.content = content
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    else:
        resp.raise_for_status.side_effect = None
    return resp


class TestRestAdapterRequest:
    def test_get_returns_parsed_json(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/"))
        adapter.session.request = MagicMock(return_value=make_response(json_data={"a": 1}))
        result = adapter.get("endpoint")
        assert result == {"a": 1}

    def test_get_returns_text_for_text_content_type(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/"))
        adapter.session.request = MagicMock(
            return_value=make_response(text="hello", content_type="text/plain")
        )
        assert adapter.get("endpoint") == "hello"

    def test_get_returns_raw_bytes_for_other_content_type(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/"))
        adapter.session.request = MagicMock(
            return_value=make_response(content=b"\x00\x01", content_type="application/zip")
        )
        assert adapter.get("endpoint") == b"\x00\x01"

    def test_request_joins_base_url_and_endpoint(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/api/"))
        mock_request = MagicMock(return_value=make_response(json_data={}))
        adapter.session.request = mock_request
        adapter.get("names.zip")
        called_url = mock_request.call_args.kwargs["url"]
        assert called_url == "https://example.com/api/names.zip"

    def test_raises_on_http_error_status(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/"))
        adapter.session.request = MagicMock(return_value=make_response(status_code=500))
        with pytest.raises(requests.HTTPError):
            adapter.get("endpoint")

    def test_post_uses_post_method(self):
        adapter = RestAdapter(RestAdapterConfig(base_url="https://example.com/"))
        mock_request = MagicMock(return_value=make_response(json_data={"ok": True}))
        adapter.session.request = mock_request
        adapter.post("endpoint", json={"x": 1})
        assert mock_request.call_args.kwargs["method"] == "POST"

    def test_custom_headers_merged_with_session_headers(self):
        config = RestAdapterConfig(base_url="https://example.com/", headers={"X-Base": "1"})
        adapter = RestAdapter(config)
        mock_request = MagicMock(return_value=make_response(json_data={}))
        adapter.session.request = mock_request
        adapter.get("endpoint", headers={"X-Extra": "2"})
        sent_headers = mock_request.call_args.kwargs["headers"]
        assert sent_headers["X-Base"] == "1"
        assert sent_headers["X-Extra"] == "2"
