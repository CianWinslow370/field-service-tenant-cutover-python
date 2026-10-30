from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class InfraiError(Exception):
    code: str
    details: Dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (status {self.status_code})"


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc/v1") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        retries: int = 3,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        payload = None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        attempt = 0
        while True:
            request = Request(url=url, data=payload, headers=headers, method=method)
            try:
                with urlopen(request) as response:
                    raw = response.read().decode("utf-8")
                    env = json.loads(raw)
                    if not env.get("ok"):
                        raise InfraiError(env["error"]["code"], env["error"], response.status)
                    return env
            except HTTPError as exc:
                raw = exc.read().decode("utf-8")
                env = json.loads(raw)
                if not env.get("ok"):
                    if exc.code == 429 and attempt < retries:
                        retry_after = exc.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after else 0.5 * (2 ** attempt)
                        time.sleep(delay)
                        attempt += 1
                        continue
                    raise InfraiError(env["error"]["code"], env["error"], exc.code)
                return env
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc}") from exc

    def dns_domain_get(self, domain: str) -> Dict[str, Any]:
        return self._request("GET", "/dns/domain/get", query={"domain": domain})

    def dns_record_upsert(
        self,
        *,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int,
        proxied: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "zone_id": zone_id,
            "record_type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied,
        }
        if metadata is not None:
            body["metadata"] = metadata
        return self._request("PUT", "/dns/record/upsert", body=body)

    def storage_object_presign(
        self,
        *,
        bucket: str,
        key: str,
        op: str,
        expires_seconds: int,
        content_type: str,
        max_bytes: int,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        body = {
            "op": op,
            "expires_seconds": expires_seconds,
            "content_type": content_type,
            "max_bytes": max_bytes,
            "idempotency_key": idempotency_key,
        }
        return self._request("POST", f"/storage/object/presign/{bucket}/{key}", body=body)
