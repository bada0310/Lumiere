import logging
from urllib.parse import urlparse

from rest_framework import status

from .exceptions import SAFE_SCRAPE_ERROR_MESSAGE, ScrapingError
from .http_client import resolve_redirect_url, validate_public_url
from .schemas import ScrapedProduct
from .scrapers import GenericBrowserScraper, OliveYoungScraper, ThreeCEScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    _registered_scraper_classes = []
    short_url_hosts = {'oy.run', 'www.oy.run'}

    def __init__(self, scraper_classes=None, fallback_scraper=None):
        classes = scraper_classes if scraper_classes is not None else self.default_scraper_classes()
        self.scrapers = [scraper_class() for scraper_class in classes]
        self.fallback_scraper = fallback_scraper or GenericBrowserScraper()

    @classmethod
    def register(cls, scraper_class):
        if scraper_class not in cls._registered_scraper_classes:
            cls._registered_scraper_classes.append(scraper_class)
        return scraper_class

    @classmethod
    def default_scraper_classes(cls):
        if not cls._registered_scraper_classes:
            cls.register(OliveYoungScraper)
            cls.register(ThreeCEScraper)
        return list(cls._registered_scraper_classes)

    @classmethod
    def default(cls):
        return cls()

    def scrape(self, url: str, *, original_url: str = '') -> ScrapedProduct:
        safe_url = validate_public_url(url)
        initial_url = original_url or safe_url
        host = (urlparse(safe_url).hostname or '').lower()

        if host in self.short_url_hosts:
            safe_url = resolve_redirect_url(safe_url)
            host = (urlparse(safe_url).hostname or '').lower()

        scraper = self._select_scraper(safe_url)
        logger.info('ScraperManager selected source=%s host=%s url=%s', scraper.source, host, safe_url)
        try:
            result = scraper.scrape(safe_url, original_url=initial_url)
        except ScrapingError:
            raise
        except Exception as exc:
            logger.exception('Unhandled scraper failure source=%s url=%s', getattr(scraper, 'source', ''), safe_url)
            raise ScrapingError(
                SAFE_SCRAPE_ERROR_MESSAGE,
                code='SCRAPER_UNHANDLED_FAILURE',
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc
        return result

    def _select_scraper(self, url):
        for scraper in self.scrapers:
            if scraper.supports(url):
                return scraper
        return self.fallback_scraper


def scrape_product_url(product_url: str) -> ScrapedProduct:
    return ScraperManager.default().scrape(product_url)
