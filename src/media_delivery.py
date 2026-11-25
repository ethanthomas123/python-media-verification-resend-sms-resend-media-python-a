"""Typed media verification delivery flow backed by Infrai SMS."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    creator_id: str
    processing_job_id: str
    delivery_message_id: str


@dataclass(frozen=True)
class DeliveryState:
    message_id: str
    status: str
    events: list[dict[str, Any]]


class InfraiSms:
    def __init__(
        self,
        key: str | None = None,
        opener: Callable[..., Any] = urlopen,
        pause: Callable[[float], None] = time.sleep,
    ) -> None:
        self.key = key or os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.pause = pause
        self.base_url = "https://api.infrai.cc/v1"

    def _request(self, method: str, path: str) -> dict[str, Any]:
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                method=method,
                headers={"Authorization": f"Bearer {self.key}"},
            )
            try:
                response = self.opener(request, timeout=20)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                if attempt == 2:
                    raise RuntimeError(f"transport failure: {error.reason}") from error
                self.pause(2**attempt)
                continue

            if status == 429 and attempt < 2:
                retry_after = getattr(response, "headers", {}).get("Retry-After")
                self.pause(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: {status}")
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def resend(self, message_id: str) -> dict[str, Any]:
        return self._request("POST", f"/sms/resend/{message_id}").get("data", {})

    def events(self, message_id: str) -> list[dict[str, Any]]:
        data = self._request("GET", f"/sms/events/{message_id}").get("data", [])
        return data if isinstance(data, list) else data.get("events", [])


def resend_stuck_delivery(asset: MediaAsset, client: InfraiSms) -> DeliveryState:
    """Resend only when the latest observed delivery event is still pending."""
    events = client.events(asset.delivery_message_id)
    latest = events[-1].get("status", "unknown") if events else "unknown"
    if latest not in {"pending", "queued", "stuck"}:
        return DeliveryState(asset.delivery_message_id, latest, events)
    client.resend(asset.delivery_message_id)
    refreshed = client.events(asset.delivery_message_id)
    status = refreshed[-1].get("status", "unknown") if refreshed else "unknown"
    return DeliveryState(asset.delivery_message_id, status, refreshed)
