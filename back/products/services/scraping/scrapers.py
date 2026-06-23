import logging
from urllib.parse import urlparse

from rest_framework import status

from products.services.product_page_parser import parse_product_page

from .base import ProductScraper
from .browser_client import render_html
from .exceptions import SAFE_SCRAPE_ERROR_MESSAGE, ScrapingError
from .http_client import fetch_text, resolve_redirect_url, retry, validate_public_url
from .schemas import ScrapedColorOption, ScrapedProduct

logger = logging.getLogger(__name__)


class OliveYoungScraper(ProductScraper):
    source = 'OLIVEYOUNG'
    domains = {'oliveyoung.co.kr', 'www.oliveyoung.co.kr', 'm.oliveyoung.co.kr', 'oy.run', 'www.oy.run'}
    short_domains = {'oy.run', 'www.oy.run'}

    def scrape(self, url: str, *, original_url: str = '') -> ScrapedProduct:
        from products.services.url_color_analysis import (
            ProductColorAnalysisError,
            build_oliveyoung_canonical_url,
            extract_oliveyoung_goods_no,
            fetch_oliveyoung_html,
            parse_oliveyoung_page,
        )

        safe_url = validate_public_url(url)
        host = (urlparse(safe_url).hostname or '').lower()
        if host in self.short_domains:
            safe_url = resolve_redirect_url(safe_url, referer='https://www.oliveyoung.co.kr/')

        goods_no = extract_oliveyoung_goods_no(safe_url)
        if not goods_no:
            raise ScrapingError(
                SAFE_SCRAPE_ERROR_MESSAGE,
                code='OLIVEYOUNG_GOODS_NO_MISSING',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        canonical_url = build_oliveyoung_canonical_url(goods_no)
        try:
            html_text, fetched_url = fetch_oliveyoung_html(canonical_url)
            parsed = parse_oliveyoung_page(html_text, fetched_url, goods_no)
        except ProductColorAnalysisError:
            logger.exception('OliveYoung scraper returned partial result goods_no=%s', goods_no)
            return ScrapedProduct(
                product_name='',
                brand='',
                options=[],
                source=self.source,
                product_url=canonical_url,
                final_url=canonical_url,
                metadata={'goods_no': goods_no, 'analysis_status': 'PARTIAL'},
            )
        except Exception as exc:
            logger.exception('OliveYoung scraper failed goods_no=%s', goods_no)
            raise ScrapingError(
                SAFE_SCRAPE_ERROR_MESSAGE,
                code='OLIVEYOUNG_SCRAPE_FAILED',
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

        return ScrapedProduct(
            product_name=parsed.product_name,
            brand=parsed.brand_name,
            options=[
                ScrapedColorOption(
                    option_name=option.option_name or option.option_no,
                    color_code=option.hex_code or None,
                    image_url=option.image_url or parsed.thumbnail_url or None,
                )
                for option in parsed.options
                if (option.option_name or option.option_no)
            ],
            source=self.source,
            product_url=canonical_url,
            final_url=fetched_url,
            metadata={'goods_no': goods_no, 'analysis_status': 'COMPLETE'},
        )


class ThreeCEScraper(ProductScraper):
    source = 'THREE_CE'
    domains = {'3cecosmetics.co.kr', 'www.3cecosmetics.co.kr'}

    def scrape(self, url: str, *, original_url: str = '') -> ScrapedProduct:
        from products.services.threece_analysis import (
            extract_selected_option,
            fetch_threece_html,
            parse_threece_page,
        )
        from products.services.url_color_analysis import ProductColorAnalysisError

        safe_url = validate_public_url(url)
        selected_option = extract_selected_option(safe_url)
        try:
            html_text, final_url = fetch_threece_html(safe_url)
            analysis = parse_threece_page(
                html_text,
                final_url,
                selected_option=selected_option,
                user_profile=None,
            )
        except ProductColorAnalysisError as exc:
            logger.exception('3CE scraper failed code=%s url=%s', getattr(exc, 'code', ''), safe_url)
            raise ScrapingError(
                SAFE_SCRAPE_ERROR_MESSAGE,
                code=getattr(exc, 'code', 'THREE_CE_SCRAPE_FAILED'),
                status_code=getattr(exc, 'status_code', status.HTTP_400_BAD_REQUEST),
            ) from exc
        except Exception as exc:
            logger.exception('3CE scraper failed url=%s', safe_url)
            raise ScrapingError(
                SAFE_SCRAPE_ERROR_MESSAGE,
                code='THREE_CE_SCRAPE_FAILED',
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

        product = analysis.get('product') or {}
        fallback_image_url = product.get('image_url') or product.get('thumbnail_url') or None
        return ScrapedProduct(
            product_name=product.get('product_name') or product.get('name') or '',
            brand=product.get('brand_name') or product.get('brand') or '3CE',
            options=[
                ScrapedColorOption(
                    option_name=option.get('display_name') or option.get('option_name') or option.get('option_no'),
                    color_code=option.get('hex_code') or None,
                    image_url=option.get('swatch_image_url') or option.get('image_url') or fallback_image_url,
                )
                for option in analysis.get('options') or []
                if option.get('option_name') or option.get('display_name')
            ],
            source=self.source,
            product_url=product.get('product_url') or final_url,
            final_url=final_url,
            metadata={
                'selected_option': analysis.get('selected_option') or selected_option,
                'analysis_status': analysis.get('analysis_status') or 'COMPLETE',
            },
        )


class GenericBrowserScraper(ProductScraper):
    source = 'GENERIC'

    def supports(self, url: str) -> bool:
        return False

    def scrape(self, url: str, *, original_url: str = '') -> ScrapedProduct:
        safe_url = validate_public_url(url)
        try:
            html_text, final_url = retry(
                lambda: render_html(safe_url),
                stage='Generic browser scrape',
                url=safe_url,
                attempts=1,
            )
        except ScrapingError:
            logger.exception('Generic browser scrape failed, falling back to HTTP url=%s', safe_url)
            html_text, final_url = retry(
                lambda: fetch_text(safe_url),
                stage='Generic HTTP scrape',
                url=safe_url,
            )

        parsed = parse_product_page(html_text, final_url)
        return ScrapedProduct(
            product_name=parsed.product_name,
            brand=parsed.brand_name,
            options=[
                ScrapedColorOption(
                    option_name=option.option_name or option.option_no,
                    color_code=option.hex_code or None,
                    image_url=option.image_url or parsed.thumbnail_url or None,
                )
                for option in parsed.options
                if (option.option_name or option.option_no)
            ],
            source=self.source,
            product_url=final_url,
            final_url=final_url,
            metadata={'analysis_status': 'COMPLETE'},
        )
