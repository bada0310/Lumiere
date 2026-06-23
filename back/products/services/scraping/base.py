from abc import ABC, abstractmethod

from .schemas import ScrapedProduct


class ProductScraper(ABC):
    source = 'GENERIC'
    domains: set[str] = set()

    def supports(self, url: str) -> bool:
        from urllib.parse import urlparse

        hostname = (urlparse(str(url or '')).hostname or '').lower()
        return hostname in self.domains

    @abstractmethod
    def scrape(self, url: str, *, original_url: str = '') -> ScrapedProduct:
        raise NotImplementedError
