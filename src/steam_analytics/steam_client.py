import os

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "http://api.steampowered.com"
RETRY_STATUSES = (429, 500, 502, 503, 504)

def _build_session(retries: int, backoff: float) -> requests.Session:
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=("GET",),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

class SteamClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 10,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        if api_key is None:
            load_dotenv()
            api_key = os.environ["STEAM_API_KEY"]
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    def _get(
        self, path: str, params: dict | None = None, *, auth: bool = False
    ) -> dict:
        params = dict(params or {})
        if auth:
            params["key"] = self.api_key
        try:
            resp = self.session.get(
            f"{BASE_URL}/{path}", params=params, timeout=self.timeout
            )
        except requests.RequestException as exc:
            # 'from None' drops the original exception,
            # whose message includes the URL and key.
            raise RuntimeError(f"Steam API {path} failed: {type(exc).__name__}") from None
        if not resp.ok:
            # Dont't use raise_for_status(): its messages includes the key
            raise RuntimeError(f"Steam API {path} returned HTTP {resp.status_code}")
        return resp.json()

    def get_current_players(self, appid: int) -> int:
        data = self._get(
            "ISteamUserStats/GetNumberOfCurrentPlayers/v1/", {"appid": appid}
        )
        return data["response"]["player_count"]

    def get_app_list(self, max_results: int = 10) -> list[dict]:
        data = self._get(
            "IStoreService/GetAppList/v1/", {"max_results": max_results}, auth=True
        )
        return data["response"]["apps"]
