import ipaddress
import logging
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import status

from .exceptions import SAFE_SCRAPE_ERROR_MESSAGE, ScrapingError

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
)


def browser_headers(referer='https://www.google.com/'):
    return {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/avif,image/webp,image/apng,*/*;q=0.8'
        ),
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': referer,
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }


def validate_public_url(raw_url):
    value = str(raw_url or '').strip()
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc or not parsed.hostname:
        raise ScrapingError('Invalid product URL.', code='INVALID_URL', status_code=status.HTTP_400_BAD_REQUEST)
    if parsed.username or parsed.password:
        raise ScrapingError('Invalid product URL.', code='INVALID_URL', status_code=status.HTTP_400_BAD_REQUEST)

    hostname = parsed.hostname.lower()
    if hostname in {'localhost', 'localhost.localdomain'}:
        raise ScrapingError('Invalid product URL.', code='INVALID_URL', status_code=status.HTTP_400_BAD_REQUEST)

    try:
        address_infos = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == 'https' else 80),
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise ScrapingError('Invalid product URL.', code='INVALID_URL', status_code=status.HTTP_400_BAD_REQUEST) from exc

    for info in address_infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ScrapingError('Invalid product URL.', code='INVALID_URL', status_code=status.HTTP_400_BAD_REQUEST)

    return urlunparse(parsed)


def fetch_text(url, *, timeout=None, max_bytes=None, referer='https://www.google.com/'):
    safe_url = validate_public_url(url)
    timeout = timeout or int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    max_bytes = max_bytes or int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_MAX_HTML_BYTES', 2_000_000))
    request = Request(safe_url, headers=browser_headers(referer))
    logger.info('Scraper HTTP fetch url=%s timeout=%s', safe_url, timeout)
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, 'status', None) or getattr(response, 'code', 200)
            if status_code >= 400:
                raise ScrapingError(
                    SAFE_SCRAPE_ERROR_MESSAGE,
                    code='FETCH_FAILED',
                    status_code=status.HTTP_502_BAD_GATEWAY,
                )
            payload = response.read(max_bytes + 1)
            content_type = response.headers.get('Content-Type', '')
            final_url = validate_public_url(response.geturl() or safe_url)
    except ScrapingError:
        raise
    except HTTPError as exc:
        logger.exception('Scraper HTTP error status=%s url=%s', exc.code, safe_url)
        raise ScrapingError(SAFE_SCRAPE_ERROR_MESSAGE, code='FETCH_FAILED', status_code=status.HTTP_502_BAD_GATEWAY) from exc
    except (URLError, TimeoutError, socket.timeout, OSError) as exc:
        logger.exception('Scraper HTTP fetch failed url=%s', safe_url)
        raise ScrapingError(SAFE_SCRAPE_ERROR_MESSAGE, code='FETCH_FAILED', status_code=status.HTTP_502_BAD_GATEWAY) from exc

    if len(payload) > max_bytes:
        raise ScrapingError(SAFE_SCRAPE_ERROR_MESSAGE, code='RESPONSE_TOO_LARGE', status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    return decode_response(payload, content_type), final_url


def resolve_redirect_url(url, *, timeout=5, referer='https://www.google.com/'):
    safe_url = validate_public_url(url)
    request = Request(safe_url, headers=browser_headers(referer))
    logger.info('Resolving scraper redirect url=%s', safe_url)
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = validate_public_url(response.geturl() or safe_url)
    except (HTTPError, URLError, TimeoutError, socket.timeout, OSError) as exc:
        logger.exception('Scraper redirect resolve failed url=%s', safe_url)
        raise ScrapingError(
            'The short URL could not be resolved.',
            code='SHORT_URL_RESOLVE_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    logger.info('Resolved scraper redirect url=%s final_url=%s', safe_url, final_url)
    return final_url


def retry(operation, *, stage, url, attempts=None, base_delay=0.5):
    attempts = attempts or int(getattr(settings, 'PRODUCT_ANALYSIS_HTTP_RETRY_ATTEMPTS', 2))
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            logger.info('%s attempt %s/%s url=%s', stage, attempt, attempts, url)
            return operation()
        except ScrapingError as exc:
            last_exc = exc
            logger.exception('%s failed attempt=%s url=%s code=%s', stage, attempt, url, exc.code)
            if attempt >= attempts:
                break
            time.sleep(base_delay * (2 ** (attempt - 1)))
    raise last_exc or ScrapingError(SAFE_SCRAPE_ERROR_MESSAGE)


def decode_response(payload, content_type):
    charset = ''
    for part in str(content_type or '').split(';'):
        part = part.strip()
        if part.lower().startswith('charset='):
            charset = part.split('=', 1)[1].strip()
            break
    try:
        return payload.decode(charset or 'utf-8', errors='replace')
    except LookupError:
        return payload.decode('utf-8', errors='replace')
