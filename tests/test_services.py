from src.repositories.memory import MemoryURLRepository, MemoryAnalyticsRepository
from src.services import URLService

def test_service():
    s = URLService(MemoryURLRepository(), MemoryAnalyticsRepository())
    r = s.shorten("https://example.com")
    assert len(r.short_code) == 7

def test_service_validation():
    s = URLService(MemoryURLRepository(), MemoryAnalyticsRepository())
    try:
        s.shorten("ftp://example.com")
        assert False
    except ValueError:
        pass

def test_service_click():
    a = MemoryAnalyticsRepository()
    s = URLService(MemoryURLRepository(), a)
    r = s.shorten("https://example.com")
    s.redirect(r.short_code, {"User-Agent": "pytest"})
    assert a.count(r.short_code) == 1
