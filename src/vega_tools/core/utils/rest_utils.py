import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class RestAdapterConfig:
    base_url: str
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Any] = None
    proxies: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[float] = None
    verify: Union[bool, str] = True
    retries: int = 3
    backoff_factor: float = 0.3


class RestAdapter:
    """
    A thin wrapper around `requests.Session()` with:
      - automatic retries
      - JSON serialization
      - unified request method
      - optional verbose logging
    """

    def __init__(self, config: RestAdapterConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.session = requests.Session()
        self.session.headers.update(config.headers)
        if config.auth:
            self.session.auth = config.auth
        if config.proxies:
            self.session.proxies.update(config.proxies)

        retry_strategy = Retry(
            total=config.retries,
            backoff_factor=config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        allow_redirects: bool = True,
    ) -> Union[Dict[str, Any], str, bytes]:
        """
        Make an HTTP request and return parsed JSON, text, or raw bytes.

        Raises:
            requests.HTTPError on 4xx/5xx (after retries).
        """
        url = urljoin(self.config.base_url, endpoint)
        req_headers = dict(self.session.headers)
        if headers:
            req_headers.update(headers)

        self.logger.debug(f"→ {method} {url} params={params} json={json or data}")
        resp = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=req_headers,
            cookies=cookies,
            timeout=timeout or self.config.timeout,
            verify=self.config.verify if self.config.verify is not True else certifi.where(),
            allow_redirects=allow_redirects,
        )
        resp.raise_for_status()
        self.logger.debug(f"← {resp.status_code} {resp.headers.get('Content-Type')}")

        ctype = resp.headers.get("Content-Type", "").lower()
        if "application/json" in ctype:
            return resp.json()
        if "text" in ctype or "html" in ctype:
            return resp.text
        return resp.content

    def get(self, endpoint: str, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs):
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)
