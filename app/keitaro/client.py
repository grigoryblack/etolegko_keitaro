"""Client for the Keitaro admin panel legacy object API.

Authentication is session based: POST /admin/?object=auth.login with
{login, password} returns a `states` cookie which is then used for all
/admin/?object=<resource> calls.
"""

from typing import Any

import httpx


class KeitaroError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Keitaro API error {status_code}: {detail}")


class KeitaroNotAuthenticated(KeitaroError):
    def __init__(self):
        super().__init__(401, "Session expired or not connected")


class KeitaroClient:
    def __init__(self, base_url: str, session_cookie: str):
        self.base_url = base_url.rstrip("/")
        self.admin_url = f"{self.base_url}/admin/"
        self.session_cookie = session_cookie

    @classmethod
    async def login(cls, base_url: str, login: str, password: str) -> "KeitaroClient":
        base_url = base_url.rstrip("/")
        admin_url = f"{base_url}/admin/"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                admin_url,
                params={"object": "auth.login"},
                json={"login": login, "password": password},
            )
        if resp.status_code >= 400:
            raise KeitaroError(resp.status_code, resp.text[:500])
        try:
            data = resp.json()
        except Exception:
            data = {}
        if not data.get("success"):
            raise KeitaroError(401, data.get("message") or "Login failed")
        cookie = resp.cookies.get("states")
        if not cookie:
            raise KeitaroError(401, "No session cookie returned by Keitaro")
        return cls(base_url, cookie)

    async def _request(
        self, method: str, obj: str, params: dict | None = None, payload: Any = None
    ) -> Any:
        query = {"object": obj}
        if params:
            query.update(params)
        headers = {
            "Cookie": f"states={self.session_cookie}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method, self.admin_url, params=query, json=payload, headers=headers
            )
        if resp.status_code == 401:
            raise KeitaroNotAuthenticated()
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise KeitaroError(resp.status_code, detail)
        if not resp.content:
            return None
        try:
            data = resp.json()
        except Exception:
            raise KeitaroError(resp.status_code, resp.text[:500])
        if isinstance(data, dict) and data.get("error"):
            raise KeitaroError(resp.status_code, data["error"])
        return data

    @staticmethod
    def _first(data: Any) -> Any:
        return data[0] if isinstance(data, list) else data

    # --- entities -------------------------------------------------------

    async def list_domains(self):
        return await self._request("GET", "domains")

    async def list_groups(self, group_type: str = "campaigns"):
        return await self._request("GET", "groups", params={"type": group_type})

    async def list_traffic_sources(self):
        try:
            return await self._request("GET", "traffic_sources")
        except KeitaroError:
            return await self._request("GET", "sources")

    async def list_offers(self):
        return await self._request("GET", "offers")

    async def get_offer(self, offer_id: int):
        data = await self._request("GET", "offers", params={"id": offer_id})
        return self._first(data)

    async def list_campaigns(self):
        return await self._request("GET", "campaigns")

    async def create_campaign(self, payload: dict):
        return await self._request("POST", "campaigns.create", payload=payload)

    async def list_streams(self, campaign_id: int):
        return await self._request(
            "GET", "streams", params={"campaign_id": campaign_id}
        )

    async def create_stream(self, payload: dict):
        return await self._request("POST", "streams.create", payload=payload)

    async def update_stream(self, stream_id: int, payload: dict):
        return await self._request(
            "PUT", "streams.update", params={"id": stream_id}, payload=payload
        )


# --- connection store ----------------------------------------------------
# Single-session store: the app is a local single-user wrapper, so the
# Keitaro connection is kept in memory. Re-login after a restart.

_current_client: KeitaroClient | None = None


def set_keitaro_client(client: KeitaroClient | None) -> None:
    global _current_client
    _current_client = client


def get_keitaro_client() -> KeitaroClient:
    if _current_client is None:
        raise KeitaroNotAuthenticated()
    return _current_client
