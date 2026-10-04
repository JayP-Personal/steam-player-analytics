import pytest
import requests
import responses

from steam_analytics.steam_client import BASE_URL, SteamClient

KEY = "test-key-123"
PLAYERS_URL = f"{BASE_URL}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
APPS_URL = f"{BASE_URL}/IStoreService/GetAppList/v1/"


@pytest.fixture
def client() -> SteamClient:
    # retries=0 keeps tests fast and deterministic; retry config is tested separately.
    return SteamClient(api_key=KEY, retries=0, backoff=0)


@responses.activate
def test_get_current_players_returns_count(client):
    responses.add(
        responses.GET,
        PLAYERS_URL,
        json={"response": {"player_count": 812345, "result": 1}},
    )

    assert client.get_current_players(730) == 812345
    sent_url = responses.calls[0].request.url
    assert "appid=730" in sent_url
    assert "key=" not in sent_url  # keyless endpoint: don't send the key


@responses.activate
def test_get_app_list_sends_key(client):
    responses.add(
        responses.GET,
        APPS_URL,
        json={"response": {"apps": [{"appid": 10, "name": "Counter-Strike"}]}},
    )

    apps = client.get_app_list(max_results=1)

    assert apps == [{"appid": 10, "name": "Counter-Strike"}]
    assert f"key={KEY}" in responses.calls[0].request.url


@responses.activate
def test_http_error_raises_without_leaking_key(client):
    responses.add(responses.GET, APPS_URL, status=403)

    with pytest.raises(RuntimeError, match="HTTP 403") as exc_info:
        client.get_app_list()

    assert KEY not in str(exc_info.value)


@responses.activate
def test_connection_error_raises_without_leaking_key(client):
    # Real requests exceptions include the full URL, key and all.
    responses.add(
        responses.GET,
        APPS_URL,
        body=requests.ConnectionError(f"Max retries exceeded: {APPS_URL}?key={KEY}"),
    )

    with pytest.raises(RuntimeError, match="ConnectionError") as exc_info:
        client.get_app_list()

    assert KEY not in str(exc_info.value)
    assert exc_info.value.__suppress_context__  # `from None` hid the original


def test_retry_config():
    client = SteamClient(api_key=KEY, retries=3, backoff=1.0)
    retry = client.session.get_adapter(BASE_URL).max_retries

    assert retry.total == 3
    assert retry.backoff_factor == 1.0
    assert {429, 500, 502, 503, 504} <= set(retry.status_forcelist)
    assert 403 not in retry.status_forcelist  # bad key should fail fast
