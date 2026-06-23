import ipaddress
import logging
import re
import socket
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, unquote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.db.models import Q
from rest_framework import status

from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.services.primary import get_primary_diagnosis_for_user
from engagements.models import UrlAnalysisRecord
from products.models import Product, ProductOffer
from products.services.recommendation import build_user_tone_profile, calculate_option_match

from .ai_color_explanations import attach_ai_explanations
from .color_extraction import ColorExtractionError, dominant_color_from_image_url
from .color_metrics import (
    build_color_metrics,
    fallback_hex_from_name,
    hex_to_rgb,
    public_grade_from_score,
)
from .product_page_parser import ParsedProductPage, ParsedOption, parse_product_page
from .threece_analysis import THREE_CE_HOSTS, is_threece_url

logger = logging.getLogger(__name__)

OLIVEYOUNG_HOSTS = {'oliveyoung.co.kr', 'www.oliveyoung.co.kr', 'm.oliveyoung.co.kr'}
OLIVEYOUNG_SHORT_HOSTS = {'oy.run', 'www.oy.run'}
OLIVEYOUNG_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
)
SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE = '상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.'
SHORT_URL_RESOLVE_ERROR_MESSAGE = '단축 링크를 해석하지 못했습니다. 전체 상품 URL을 입력해주세요.'
OLIVEYOUNG_PARTIAL_MESSAGE = '상품 번호를 확인했습니다. 상세 상품 정보는 자동으로 가져오지 못했습니다.'
PRODUCT_ANALYSIS_DISCLAIMER = (
    '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. '
    'AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.'
)


class ProductColorAnalysisError(RuntimeError):
    def __init__(self, message, *, code='analysis_failed', status_code=status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def normalize_product_url(raw_url):
    original_url = str(raw_url or '').strip()
    candidate_url = original_url
    decoded_for_host_check = unquote(original_url)
    if candidate_url and '://' not in candidate_url and _starts_with_supported_host(decoded_for_host_check):
        candidate_url = f'https://{candidate_url}'

    logger.info('Normalizing product URL: %s', original_url)
    normalized_url = validate_public_url(candidate_url)
    parsed = urlparse(normalized_url)
    host = (parsed.hostname or '').lower()

    if host in OLIVEYOUNG_SHORT_HOSTS:
        logger.info('Resolving OliveYoung short URL: %s', normalized_url)
        normalized_url = resolve_short_url(normalized_url)
        parsed = urlparse(normalized_url)
        host = (parsed.hostname or '').lower()

    if host in OLIVEYOUNG_HOSTS:
        goods_no = extract_oliveyoung_goods_no(normalized_url)
        if goods_no:
            normalized_url = build_oliveyoung_canonical_url(goods_no)
            logger.info('Canonicalized OliveYoung URL with goodsNo=%s: %s', goods_no, normalized_url)

    return {
        'original_url': original_url,
        'normalized_url': normalized_url,
    }


def resolve_short_url(url):
    logger.info('Resolving short product URL via GET redirect: %s', url)
    request = Request(url, headers=_browser_like_headers('https://www.oliveyoung.co.kr/'))
    try:
        with urlopen(request, timeout=5) as response:
            final_url = response.geturl() or url
            logger.info('Resolved short URL to: %s', final_url)
    except (HTTPError, URLError, TimeoutError, socket.timeout, OSError) as exc:
        logger.exception('Short URL resolve failed: %s', url)
        raise ProductColorAnalysisError(
            '단축 링크를 해석하지 못했습니다.',
            code='SHORT_URL_RESOLVE_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return validate_public_url(final_url)


def is_oliveyoung_url(url):
    return (urlparse(str(url or '')).hostname or '').lower() in OLIVEYOUNG_HOSTS


def extract_oliveyoung_goods_no(url):
    parsed = urlparse(str(url or ''))
    query = parse_qs(parsed.query)
    goods_values = query.get('goodsNo') or query.get('goodsno') or []
    return str(goods_values[0] if goods_values else '').strip()


def build_oliveyoung_canonical_url(goods_no):
    return urlunparse(
        (
            'https',
            'www.oliveyoung.co.kr',
            '/store/goods/getGoodsDetail.do',
            '',
            urlencode({'goodsNo': goods_no}),
            '',
        )
    )


def _starts_with_supported_host(value):
    host = value.split('/', 1)[0].split('?', 1)[0].lower()
    return host in OLIVEYOUNG_HOSTS or host in OLIVEYOUNG_SHORT_HOSTS or host in THREE_CE_HOSTS


def _browser_like_headers(referer='https://www.oliveyoung.co.kr/'):
    return {
        'User-Agent': OLIVEYOUNG_USER_AGENT,
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


def _retry(operation, *, stage, url, attempts=2, base_delay=0.5):
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            logger.info('%s attempt %s/%s: %s', stage, attempt, attempts, url)
            return operation()
        except ProductColorAnalysisError as exc:
            last_exc = exc
            logger.exception('%s failed on attempt %s/%s: %s', stage, attempt, attempts, url)
            if attempt >= attempts:
                break
            time.sleep(base_delay * (2 ** (attempt - 1)))
    raise last_exc


def analyze_product_color_url(product_url, *, user=None):
    normalized = normalize_product_url(product_url)
    if is_threece_url(normalized['normalized_url']):
        logger.info('Dispatching 3CE analysis for URL: %s', normalized['normalized_url'])
        from .threece_analysis import ThreeCEAnalyzer

        return ThreeCEAnalyzer().analyze(
            normalized['normalized_url'],
            original_url=normalized['original_url'],
            user=user,
        )

    if is_oliveyoung_url(normalized['normalized_url']):
        logger.info('Dispatching OliveYoung analysis for URL: %s', normalized['normalized_url'])
        return analyze_oliveyoung_url(normalized, user=user)

    primary_payload = _primary_tone_payload(user)
    user_profile = _build_user_profile(primary_payload)
    user_tone = _build_user_tone_response(primary_payload)
    try:
        from products.services.scraping import ScrapingError, scrape_product_url

        scraped = scrape_product_url(normalized['normalized_url'])
    except ScrapingError as exc:
        logger.exception('Generic scraping manager failed code=%s url=%s', exc.code, normalized['normalized_url'])
        raise ProductColorAnalysisError(
            SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
            code=exc.code,
            status_code=exc.status_code,
        ) from exc
    return _analysis_from_scraped_product(
        scraped,
        normalized=normalized,
        primary_payload=primary_payload,
        user_profile=user_profile,
        user_tone=user_tone,
        user=user,
    )

    safe_url = validate_public_url(normalized['normalized_url'])
    logger.info('Fetching generic product page: %s', safe_url)
    html_text, final_url = fetch_html(safe_url)
    parsed = parse_product_page(html_text, final_url)

    primary_payload = _primary_tone_payload(user)
    user_profile = _build_user_profile(primary_payload)
    user_tone = _build_user_tone_response(primary_payload)
    goods_no = ''
    product_payload = {
        'url': final_url,
        'brand_name': parsed.brand_name,
        'product_name': parsed.product_name or '분석한 제품',
        'name': parsed.product_name or f'OliveYoung 상품 {goods_no}',
        'description': parsed.description,
        'thumbnail_url': parsed.thumbnail_url,
    }
    product_payload['name'] = parsed.product_name or '분석한 제품'
    product_payload['name'] = product_payload.get('product_name') or product_payload.get('name') or ''
    if not parsed.product_name:
        product_payload['product_name'] = '분석한 제품'
        product_payload['name'] = '분석한 제품'
    options = _build_option_payloads(parsed, user_profile)
    if user_profile:
        options, ai_status = attach_ai_explanations(options, product=product_payload, user_tone=user_tone)
    else:
        options, ai_status = attach_ai_explanations(options, product=product_payload, user_tone=None)

    best_option = _best_option(options)
    result = {
        'success': True,
        'source': 'GENERIC',
        'original_url': normalized['original_url'],
        'normalized_url': final_url,
        'product': product_payload,
        'product_url': final_url,
        'user_tone': user_tone,
        'personalized': bool(user_profile),
        'analysis_status': 'COMPLETE',
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': _chart_zones(primary_payload),
        },
        'options': options,
        'best_option': best_option,
        'recommendation_groups': _recommendation_groups(options),
        'ai_explanation_status': ai_status,
        'message': '상품 정보를 분석했습니다.',
        'disclaimer': '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.',
    }
    result['message'] = '상품 정보를 분석했습니다.'
    result['disclaimer'] = PRODUCT_ANALYSIS_DISCLAIMER
    _save_analysis_record(user, final_url, parsed, options, result)
    return result


def analyze_oliveyoung_url(normalized, *, user=None):
    final_url = normalized['normalized_url']
    logger.info('Starting OliveYoung product analysis: %s', final_url)
    goods_no = extract_oliveyoung_goods_no(final_url)
    if not goods_no:
        raise ProductColorAnalysisError(
            '올리브영 상품 번호를 찾을 수 없습니다.',
            code='OLIVEYOUNG_GOODS_NO_MISSING',
        )

    canonical_url = build_oliveyoung_canonical_url(goods_no)
    primary_payload = _primary_tone_payload(user)
    user_profile = _build_user_profile(primary_payload)
    user_tone = _build_user_tone_response(primary_payload)
    partial_result = _build_oliveyoung_partial_result(
        normalized=normalized,
        canonical_url=canonical_url,
        goods_no=goods_no,
        user_tone=user_tone,
        primary_payload=primary_payload,
    )
    try:
        html_text, fetched_url = fetch_oliveyoung_html(canonical_url)
    except ProductColorAnalysisError:
        logger.exception('OliveYoung HTML fetch failed for goodsNo=%s url=%s', goods_no, canonical_url)
        _save_partial_oliveyoung_analysis_record(user, canonical_url, goods_no, partial_result)
        return partial_result
    try:
        logger.info('Parsing OliveYoung product page: %s', fetched_url)
        parsed = parse_oliveyoung_page(html_text, fetched_url, goods_no)
    except Exception:
        logger.exception('OliveYoung parsing failed for goodsNo=%s url=%s', goods_no, fetched_url)
        _save_partial_oliveyoung_analysis_record(user, canonical_url, goods_no, partial_result)
        return partial_result
    matched_product = match_catalog_product(goods_no=goods_no, parsed=parsed)

    product_payload = {
        'url': canonical_url,
        'product_url': canonical_url,
        'brand_name': parsed.brand_name,
        'brand': parsed.brand_name,
        'product_name': parsed.product_name or f'올리브영 상품 {goods_no}',
        'description': parsed.description,
        'thumbnail_url': parsed.thumbnail_url,
        'image_url': parsed.thumbnail_url,
        'category': Product.Category.LIP,
        'texture': '립틴트',
    }
    product_payload['name'] = product_payload.get('product_name') or product_payload.get('name') or ''
    options = _build_option_payloads(parsed, user_profile)
    if user_profile and options:
        options, ai_status = attach_ai_explanations(options, product=product_payload, user_tone=user_tone)
    else:
        ai_status = 'skipped'

    result = {
        'success': True,
        'source': 'OLIVEYOUNG',
        'goods_no': goods_no,
        'original_url': normalized['original_url'],
        'normalized_url': canonical_url,
        'final_url': fetched_url,
        'matched_product_id': matched_product['id'] if matched_product else None,
        'matched_product': matched_product,
        'product': product_payload,
        'product_url': canonical_url,
        'user_tone': user_tone,
        'personalized': bool(user_profile),
        'analysis_status': 'COMPLETE',
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': _chart_zones(primary_payload),
        },
        'options': options,
        'best_option': _best_option(options),
        'recommendation_groups': _recommendation_groups(options),
        'ai_explanation_status': ai_status,
        'message': '상품 정보를 분석했습니다.',
        'disclaimer': '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.',
    }
    result['message'] = '상품 정보를 분석했습니다.'
    result['disclaimer'] = PRODUCT_ANALYSIS_DISCLAIMER
    _save_analysis_record(user, canonical_url, parsed, options, result)
    return result


def fetch_oliveyoung_html(url):
    attempts = int(getattr(settings, 'PRODUCT_ANALYSIS_HTTP_RETRY_ATTEMPTS', 2))
    timeout = int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    try:
        return _retry(
            lambda: fetch_oliveyoung_with_http(url, timeout=timeout),
            stage='OliveYoung HTTP fetch',
            url=url,
            attempts=attempts,
        )
    except ProductColorAnalysisError as http_exc:
        logger.exception('OliveYoung HTTP fetch exhausted: %s', url)
        if not getattr(settings, 'PRODUCT_ANALYSIS_ENABLE_BROWSER_FETCH', True):
            raise http_exc
        try:
            return _retry(
                lambda: fetch_oliveyoung_with_browser(url, timeout=timeout),
                stage='OliveYoung browser fetch',
                url=url,
                attempts=1,
            )
        except ProductColorAnalysisError:
            logger.exception('OliveYoung browser fetch failed: %s', url)
            raise http_exc


def fetch_oliveyoung_with_http(url, *, timeout):
    max_bytes = int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_MAX_HTML_BYTES', 2_000_000))
    logger.info('Fetching OliveYoung product HTML: %s', url)
    request = Request(
        url,
        headers=_browser_like_headers('https://www.oliveyoung.co.kr/'),
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, 'status', None) or getattr(response, 'code', 200)
            if status_code != 200:
                raise _oliveyoung_status_error(status_code)
            content_type = response.headers.get('Content-Type', '')
            payload = response.read(max_bytes + 1)
            final_url = validate_public_url(response.geturl() or url)
            logger.info('Fetched OliveYoung product HTML status=%s final_url=%s', status_code, final_url)
    except HTTPError as exc:
        logger.exception('OliveYoung HTTP error status=%s url=%s', exc.code, url)
        raise _oliveyoung_status_error(exc.code) from exc
    except (TimeoutError, socket.timeout) as exc:
        logger.exception('OliveYoung fetch timeout: %s', url)
        raise ProductColorAnalysisError(
            '올리브영 상품 정보를 불러오는 데 시간이 오래 걸립니다.',
            code='OLIVEYOUNG_FETCH_TIMEOUT',
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    except ProductColorAnalysisError:
        raise
    except (URLError, OSError) as exc:
        logger.exception('OliveYoung fetch failed: %s', url)
        raise ProductColorAnalysisError(
            '올리브영 상품 정보를 불러오지 못했습니다.',
            code='OLIVEYOUNG_FETCH_FAILED',
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc

    if len(payload) > max_bytes:
        raise ProductColorAnalysisError(
            '올리브영 상품 페이지 응답이 너무 큽니다.',
            code='OLIVEYOUNG_FETCH_FAILED',
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    html_text = _decode_response(payload, content_type)
    return html_text, final_url


def fetch_oliveyoung_with_browser(url, *, timeout):
    logger.info('Fetching OliveYoung product HTML with headless browser: %s', url)
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as exc:
        raise ProductColorAnalysisError(
            SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
            code='OLIVEYOUNG_BROWSER_UNAVAILABLE',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    driver = None
    try:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1365,900')
        options.add_argument('--lang=ko-KR')
        options.add_argument(f'--user-agent={OLIVEYOUNG_USER_AGENT}')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        WebDriverWait(driver, timeout).until(lambda browser: browser.execute_script('return document.readyState') == 'complete')
        html_text = driver.page_source or ''
        final_url = validate_public_url(driver.current_url or url)
    except Exception as exc:
        raise ProductColorAnalysisError(
            SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
            code='OLIVEYOUNG_BROWSER_FETCH_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                logger.warning('Failed to close OliveYoung browser driver', exc_info=True)

    if not html_text.strip():
        raise ProductColorAnalysisError(
            SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
            code='OLIVEYOUNG_BROWSER_FETCH_EMPTY',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    logger.info('Fetched OliveYoung product HTML with browser final_url=%s', final_url)
    return html_text, final_url


def parse_oliveyoung_page(html_text, source_url, goods_no):
    parsed = parse_product_page(html_text, source_url)
    brand = parsed.brand_name or _first_regex_group(
        html_text,
        [
            r'"brand"\s*:\s*"([^"]+)"',
            r"'brand'\s*:\s*'([^']+)'",
            r'<p[^>]+class="[^"]*prd_brand[^"]*"[^>]*>(.*?)</p>',
            r'<span[^>]+class="[^"]*brand[^"]*"[^>]*>(.*?)</span>',
        ],
    )
    name = parsed.product_name or _first_regex_group(
        html_text,
        [
            r'"name"\s*:\s*"([^"]+)"',
            r'<p[^>]+class="[^"]*prd_name[^"]*"[^>]*>(.*?)</p>',
            r'<p[^>]+class="[^"]*goods_name[^"]*"[^>]*>(.*?)</p>',
            r'<h1[^>]*>(.*?)</h1>',
        ],
    )
    image = parsed.thumbnail_url or _first_regex_group(
        html_text,
        [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'"image"\s*:\s*"([^"]+)"',
            r'<img[^>]+id=["\']mainImg["\'][^>]+src=["\']([^"\']+)["\']',
        ],
    )
    description = parsed.description or _first_regex_group(
        html_text,
        [
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        ],
    )

    option_names = _extract_oliveyoung_option_names(html_text)
    options = [
        ParsedOption(option_no=_option_no_from_name(option_name), option_name=option_name)
        for option_name in option_names
    ]

    return ParsedProductPage(
        url=source_url,
        brand_name=_clean_html_text(brand),
        product_name=_clean_html_text(name) or f'올리브영 상품 {goods_no}',
        description=_clean_html_text(description),
        thumbnail_url=urljoin(source_url, _clean_html_text(image)) if image else '',
        options=options[:10],
    )


def match_catalog_product(*, goods_no, parsed):
    offer = ProductOffer.objects.select_related('option__product').filter(
        Q(product_url__icontains=goods_no) | Q(naver_product_id=goods_no),
    ).first()
    product = offer.option.product if offer else None

    if product is None:
        product = Product.objects.filter(
            Q(product_url__icontains=goods_no) | Q(naver_product_id=goods_no),
        ).first()

    if product is None and parsed.product_name:
        queryset = Product.objects.filter(name__icontains=parsed.product_name[:80])
        if parsed.brand_name:
            queryset = queryset.filter(brand__icontains=parsed.brand_name)
        product = queryset.first()

    if product is None:
        return None

    return {
        'id': product.id,
        'brand_name': product.brand,
        'product_name': product.name,
        'thumbnail_url': product.display_image_url,
        'product_url': product.product_url,
    }


def _oliveyoung_status_error(status_code):
    if status_code == 403:
        return ProductColorAnalysisError(
            '올리브영 상품 페이지 접근이 제한되었습니다.',
            code='OLIVEYOUNG_FETCH_FORBIDDEN',
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    if status_code == 429:
        return ProductColorAnalysisError(
            '올리브영 요청이 일시적으로 제한되었습니다.',
            code='OLIVEYOUNG_FETCH_RATE_LIMITED',
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    return ProductColorAnalysisError(
        '올리브영 상품 정보를 불러오지 못했습니다.',
        code='OLIVEYOUNG_FETCH_FAILED',
        status_code=status.HTTP_502_BAD_GATEWAY,
    )


def _decode_response(payload, content_type):
    charset = _charset_from_content_type(content_type)
    try:
        return payload.decode(charset or 'utf-8', errors='replace')
    except LookupError:
        return payload.decode('utf-8', errors='replace')


def _first_regex_group(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text or '', flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    return ''


def _extract_oliveyoung_option_names(html_text):
    patterns = [
        r'"itemName"\s*:\s*"([^"]+)"',
        r'"optionName"\s*:\s*"([^"]+)"',
        r'"optNm"\s*:\s*"([^"]+)"',
        r'<option[^>]*>\s*([^<]+)\s*</option>',
    ]
    seen = set()
    options = []
    for pattern in patterns:
        for match in re.finditer(pattern, html_text or '', flags=re.IGNORECASE | re.DOTALL):
            name = _clean_html_text(match.group(1))
            if not name or _is_placeholder_option(name):
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            options.append(name)
    return options


def _option_no_from_name(option_name):
    match = re.search(r'(?:no\.?\s*)?(\d{1,3})', option_name or '', flags=re.IGNORECASE)
    return match.group(1).zfill(2) if match else ''


def _build_oliveyoung_partial_result(*, normalized, canonical_url, goods_no, user_tone, primary_payload):
    product_payload = {
        'url': canonical_url,
        'product_url': canonical_url,
        'brand_name': '',
        'brand': '',
        'product_name': '',
        'name': '',
        'description': '',
        'thumbnail_url': '',
        'image_url': '',
        'category': '',
        'texture': '',
    }
    result = {
        'success': True,
        'source': 'OLIVEYOUNG',
        'goods_no': goods_no,
        'original_url': normalized['original_url'],
        'normalized_url': canonical_url,
        'final_url': canonical_url,
        'matched_product_id': None,
        'matched_product': None,
        'product': product_payload,
        'product_url': canonical_url,
        'user_tone': user_tone,
        'personalized': bool(user_tone),
        'analysis_status': 'PARTIAL',
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': _chart_zones(primary_payload),
        },
        'options': [],
        'best_option': None,
        'recommendation_groups': {'BEST': [], 'GOOD': [], 'CAUTION': []},
        'ai_explanation_status': 'skipped',
        'message': OLIVEYOUNG_PARTIAL_MESSAGE,
        'disclaimer': PRODUCT_ANALYSIS_DISCLAIMER,
        'message': '상품 번호를 확인했습니다. 상세 상품 정보는 자동으로 가져오지 못했습니다.',
        'disclaimer': '?붾㈃???됱긽? ?ㅼ젣? ?ㅻ? ???덉쑝硫? 媛쒖씤李④? ?덉쓣 ???덉뒿?덈떎. AI 遺꾩꽍 寃곌낵??李멸퀬?⑹씠硫??ㅼ젣 諛쒖깋? ?쇰??? 議곕챸, 紐⑤땲???섍꼍???곕씪 ?щ씪吏????덉뒿?덈떎.',
    }
    result['message'] = OLIVEYOUNG_PARTIAL_MESSAGE
    result['disclaimer'] = PRODUCT_ANALYSIS_DISCLAIMER
    return result


def _save_partial_oliveyoung_analysis_record(user, canonical_url, goods_no, result):
    parsed = ParsedProductPage(
        url=canonical_url,
        brand_name='',
        product_name=f'OliveYoung {goods_no}',
        description='',
        thumbnail_url='',
        options=[],
    )
    _save_analysis_record(user, canonical_url, parsed, [], result)


def _clean_html_text(value):
    import html as html_module
    import re

    cleaned = re.sub(r'<[^>]+>', ' ', str(value or ''))
    cleaned = html_module.unescape(cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def _is_placeholder_option(value):
    normalized = str(value or '').lower()
    return any(token in normalized for token in ['선택', 'option', 'choose', 'select', '품절', 'sold out'])


def validate_public_url(raw_url):
    value = str(raw_url or '').strip()
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc or not parsed.hostname:
        raise ProductColorAnalysisError(
            '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
            code='invalid_url',
        )
    if parsed.username or parsed.password:
        raise ProductColorAnalysisError(
            '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
            code='invalid_url',
        )

    hostname = parsed.hostname.lower()
    if hostname in {'localhost', 'localhost.localdomain'}:
        raise ProductColorAnalysisError(
            '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
            code='invalid_url',
        )
    try:
        address_infos = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ProductColorAnalysisError(
            '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
            code='invalid_url',
        ) from exc

    for info in address_infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ProductColorAnalysisError(
                '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
                code='invalid_url',
            )

    return urlunparse(parsed)


def fetch_html(url):
    max_bytes = int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_MAX_HTML_BYTES', 2_000_000))
    timeout = int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_FETCH_TIMEOUT', 10))
    request = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 LumiereColorMatcher/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get('Content-Type', '')
            payload = response.read(max_bytes + 1)
            final_url = validate_public_url(response.geturl() or url)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProductColorAnalysisError(
            '제품 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.',
            code='fetch_failed',
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc

    if len(payload) > max_bytes:
        raise ProductColorAnalysisError(
            '제품 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.',
            code='response_too_large',
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    charset = _charset_from_content_type(content_type)
    try:
        html_text = payload.decode(charset or 'utf-8', errors='replace')
    except LookupError:
        html_text = payload.decode('utf-8', errors='replace')
    return html_text, final_url


def _analysis_from_scraped_product(scraped, *, normalized, primary_payload, user_profile, user_tone, user=None):
    final_url = scraped.final_url or scraped.product_url or normalized['normalized_url']
    first_image_url = next((option.image_url for option in scraped.options if option.image_url), '')
    product_name = scraped.product_name or 'Analyzed product'
    product_payload = {
        'url': final_url,
        'product_url': final_url,
        'brand_name': scraped.brand,
        'brand': scraped.brand,
        'product_name': product_name,
        'name': product_name,
        'description': '',
        'thumbnail_url': first_image_url,
        'image_url': first_image_url,
        'category': Product.Category.LIP,
        'texture': '',
    }
    options = _build_option_payloads_from_scraped(scraped, user_profile)
    if user_profile and options:
        options, ai_status = attach_ai_explanations(options, product=product_payload, user_tone=user_tone)
    else:
        ai_status = 'skipped'

    result = {
        'success': True,
        'source': scraped.source or 'GENERIC',
        'original_url': normalized['original_url'],
        'normalized_url': final_url,
        'final_url': final_url,
        'product': product_payload,
        'product_url': final_url,
        'user_tone': user_tone,
        'personalized': bool(user_profile),
        'analysis_status': scraped.metadata.get('analysis_status') or 'COMPLETE',
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': _chart_zones(primary_payload),
        },
        'options': options,
        'best_option': _best_option(options),
        'recommendation_groups': _recommendation_groups(options),
        'ai_explanation_status': ai_status,
        'message': '?곹뭹 ?뺣낫瑜?遺꾩꽍?덉뒿?덈떎.',
        'disclaimer': PRODUCT_ANALYSIS_DISCLAIMER,
    }
    parsed = ParsedProductPage(
        url=final_url,
        brand_name=scraped.brand,
        product_name=product_name,
        description='',
        thumbnail_url=first_image_url,
        options=[],
    )
    _save_analysis_record(user, final_url, parsed, options, result)
    return result


def _build_option_payloads_from_scraped(scraped, user_profile):
    options = []
    for index, scraped_option in enumerate(scraped.options, start=1):
        label = scraped_option.option_name or f'{index:02d}'
        image_url = scraped_option.image_url or ''
        rgb = hex_to_rgb(scraped_option.color_code)
        if not rgb and image_url:
            try:
                safe_image_url = validate_public_url(image_url)
                rgb = dominant_color_from_image_url(safe_image_url, timeout=5)
            except (ProductColorAnalysisError, ColorExtractionError) as exc:
                logger.info('Scraped option image color extraction failed: %s', exc)

        option_id = f'scraped-option-{index:02d}'
        if not rgb:
            options.append(
                {
                    'id': option_id,
                    'option_no': f'{index:02d}',
                    'option_name': label,
                    'image_url': image_url,
                    'hex_code': None,
                    'rgb': None,
                    'brightness': None,
                    'saturation': None,
                    'coolness': None,
                    'warmth': None,
                    'depth': None,
                    'softness': None,
                    'contrast': None,
                    'chart_x': None,
                    'chart_y': None,
                    'color_metrics': None,
                    'match_score': None,
                    'grade': 'PENDING',
                    'reason': 'Color HEX analysis is pending.',
                    'analysis_status': 'PENDING_COLOR_ANALYSIS',
                }
            )
            continue

        metrics = build_color_metrics(rgb)
        option_object = SimpleNamespace(
            product=SimpleNamespace(category=Product.Category.LIP),
            analyzed_tone_tag=metrics['analyzed_tone_tag'],
            brightness=metrics['brightness'],
            saturation=metrics['saturation'],
            coolness=metrics['coolness'],
            warmth=metrics['warmth'],
            depth=metrics['depth'],
            softness=metrics['softness'],
            contrast=metrics['contrast'],
        )
        if user_profile:
            match = calculate_option_match(option_object, user_profile, Product.Category.LIP)
            match_score = match['match_score']
            grade = public_grade_from_score(match_score)
            reason = match['reason']
        else:
            match_score = None
            grade = ''
            reason = 'Set a primary personal color result to calculate a personalized recommendation score.'
        options.append(
            {
                'id': option_id,
                'option_no': f'{index:02d}',
                'option_name': label,
                'image_url': image_url,
                **metrics,
                'color_metrics': metrics,
                'match_score': match_score,
                'grade': grade,
                'reason': reason,
                'analysis_status': 'DONE',
            }
        )
    return options


def _build_option_payloads(parsed, user_profile):
    options = []
    for index, parsed_option in enumerate(parsed.options, start=1):
        option_id = parsed_option.option_no or f'{index:02d}'
        label = ' '.join(part for part in [parsed_option.option_no, parsed_option.option_name] if part) or f'{index:02d}'
        rgb = _resolve_option_rgb(parsed_option, parsed.thumbnail_url)
        metrics = build_color_metrics(rgb)
        option_object = SimpleNamespace(
            product=SimpleNamespace(category=Product.Category.LIP),
            analyzed_tone_tag=metrics['analyzed_tone_tag'],
            brightness=metrics['brightness'],
            saturation=metrics['saturation'],
            coolness=metrics['coolness'],
            warmth=metrics['warmth'],
            depth=metrics['depth'],
            softness=metrics['softness'],
            contrast=metrics['contrast'],
        )

        if user_profile:
            match = calculate_option_match(option_object, user_profile, Product.Category.LIP)
            match_score = match['match_score']
            grade = public_grade_from_score(match_score)
            reason = match['reason']
        else:
            match_score = None
            grade = ''
            reason = '메인 퍼스널컬러가 설정되면 개인화 추천 이유를 확인할 수 있습니다.'

        options.append(
            {
                'id': option_id,
                'option_no': parsed_option.option_no or f'{index:02d}',
                'option_name': parsed_option.option_name or label,
                'image_url': parsed_option.image_url or parsed.thumbnail_url,
                **metrics,
                'match_score': match_score,
                'grade': grade,
                'reason': reason,
            }
        )
    return options


def _resolve_option_rgb(parsed_option, fallback_image_url):
    direct_rgb = hex_to_rgb(parsed_option.hex_code)
    if direct_rgb:
        return direct_rgb

    fallback_hex = fallback_hex_from_name(f'{parsed_option.option_no} {parsed_option.option_name}')
    fallback_rgb = hex_to_rgb(fallback_hex)
    if fallback_rgb:
        return fallback_rgb

    image_url = parsed_option.image_url or fallback_image_url
    try:
        safe_image_url = validate_public_url(image_url) if image_url else ''
        if safe_image_url:
            return dominant_color_from_image_url(safe_image_url)
    except (ProductColorAnalysisError, ColorExtractionError) as exc:
        logger.info('Option image color extraction failed: %s', exc)

    return 198, 83, 103


def _primary_tone_payload(user):
    if not user or not user.is_authenticated:
        return None
    diagnosis = get_primary_diagnosis_for_user(user)
    if not diagnosis:
        return None
    diagnosis_json = diagnosis.diagnosis_json or {}
    return build_tone_result_payload(
        diagnosis.tone_key or diagnosis.personal_color_code,
        diagnosis_json.get('second_tone_key'),
    ) | {'diagnosis_id': diagnosis.id}


def _build_user_profile(primary_payload):
    if not primary_payload:
        return None
    return build_user_tone_profile(
        tone_key=primary_payload.get('tone_key'),
        second_tone_key=primary_payload.get('second_tone_key'),
        axis_profile=primary_payload.get('axis_profile'),
        range_profile=primary_payload.get('range_profile'),
    )


def _build_user_tone_response(primary_payload):
    if not primary_payload:
        return None
    return {
        'diagnosis_id': primary_payload.get('diagnosis_id'),
        'tone_key': primary_payload.get('tone_key'),
        'tone_label': primary_payload.get('tone_label'),
        'tone_name': primary_payload.get('tone_label'),
        'second_tone_key': primary_payload.get('second_tone_key'),
        'second_tone_label': primary_payload.get('second_tone_label'),
        'axis_profile': primary_payload.get('axis_profile'),
        'range_profile': primary_payload.get('range_profile'),
        'recommended_color_families': primary_payload.get('recommended_color_families', []),
        'caution_color_families': primary_payload.get('caution_color_families', []),
    }


def _chart_zones(primary_payload):
    if not primary_payload:
        return []
    range_profile = primary_payload.get('range_profile') or {}
    return [
        {'type': 'GOOD', 'range': range_profile.get('good')},
        {'type': 'BEST', 'range': range_profile.get('best')},
    ]


def _recommendation_groups(options):
    groups = {'BEST': [], 'GOOD': [], 'CAUTION': [], 'PENDING': []}
    for option in options:
        grade = option.get('grade')
        if option.get('analysis_status') == 'PENDING_COLOR_ANALYSIS' or grade == 'PENDING':
            groups['PENDING'].append(option.get('id'))
            continue
        if grade in groups:
            groups[grade].append(option.get('id'))
    return groups


def _best_option(options):
    scored = [option for option in options if option.get('match_score') is not None]
    if not scored:
        return options[0] if options else None
    return max(scored, key=lambda option: option.get('match_score') or 0)


def _save_analysis_record(user, source_url, parsed, options, result):
    if not user or not user.is_authenticated:
        return
    try:
        UrlAnalysisRecord.objects.create(
            user=user,
            source_url=source_url,
            title=parsed.product_name or source_url,
            brand=parsed.brand_name,
            product_name=parsed.product_name,
            image_url=parsed.thumbnail_url,
            colors=[
                {
                    'option_id': option.get('id'),
                    'option_name': option.get('option_name'),
                    'hex_code': option.get('hex_code'),
                    'rgb': option.get('rgb'),
                    'brightness': option.get('brightness'),
                    'saturation': option.get('saturation'),
                    'coolness': option.get('coolness'),
                }
                for option in options
            ],
            result_payload=result,
        )
    except Exception as exc:
        logger.warning('Failed to save product URL analysis record: %s', exc)


def _charset_from_content_type(content_type):
    for part in str(content_type or '').split(';'):
        part = part.strip()
        if part.lower().startswith('charset='):
            return part.split('=', 1)[1].strip()
    return ''
