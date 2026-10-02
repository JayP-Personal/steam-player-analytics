from steam_analytics.health import check_status


def test_check_status():
    assert check_status() == "ready"