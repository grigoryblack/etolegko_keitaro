"""Thin async client for the Keitaro Admin API v1."""

from typing import Any

import httpx

from .config import settings


class KeitaroError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Keitaro API error {status_code}: {detail}")


class KeitaroClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.keitaro_api_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.keitaro_api_key

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise KeitaroError(response.status_code, detail)
        if not response.content:
            return None
        return response.json()

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, payload: dict | None = None) -> Any:
        return await self._request("POST", path, json=payload or {})

    async def put(self, path: str, payload: dict | None = None) -> Any:
        return await self._request("PUT", path, json=payload or {})

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    # --- entities -------------------------------------------------------

    async def list_domains(self):
        return await self.get("/domains")

    async def list_groups(self, group_type: str = "campaigns"):
        return await self.get("/groups", params={"type": group_type})

    async def list_traffic_sources(self):
        return await self.get("/traffic_sources")

    async def list_offers(self):
        return await self.get("/offers")

    async def list_campaigns(self):
        return await self.get("/campaigns")

    async def get_campaign(self, campaign_id: int):
        return await self.get(f"/campaigns/{campaign_id}")

    async def create_campaign(self, payload: dict):
        return await self.post("/campaigns", payload)

    async def list_streams(self, campaign_id: int):
        return await self.get(f"/campaigns/{campaign_id}/streams")

    async def get_stream(self, stream_id: int):
        return await self.get(f"/streams/{stream_id}")

    async def create_stream(self, payload: dict):
        return await self.post("/streams", payload)

    async def update_stream(self, stream_id: int, payload: dict):
        return await self.put(f"/streams/{stream_id}", payload)


def get_keitaro_client() -> KeitaroClient:
    return KeitaroClient()
