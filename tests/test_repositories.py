from src.repositories.memory import MemoryURLRepository, MemoryAnalyticsRepository

def test_url_repository():
    r = MemoryURLRepository()
    x = r.create("abc1234", "https://example.com")
    assert r.get("abc1234") == x
    assert r.exists("abc1234")
    assert r.count() == 1

def test_duplicate_rejected():
    r = MemoryURLRepository()
    r.create("abc1234", "https://example.com")
    try:
        r.create("abc1234", "https://example.org")
        assert False
    except ValueError:
        pass

def test_analytics_repository():
    r = MemoryAnalyticsRepository()
    e = r.record_click("abc1234", "pytest")
    assert e.short_code == "abc1234"
    assert r.count("abc1234") == 1
