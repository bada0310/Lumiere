import html
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

from .color_metrics import normalize_hex


@dataclass
class ParsedOption:
    option_no: str = ''
    option_name: str = ''
    image_url: str = ''
    hex_code: str = ''


@dataclass
class ParsedProductPage:
    url: str
    brand_name: str = ''
    product_name: str = ''
    description: str = ''
    thumbnail_url: str = ''
    options: list[ParsedOption] = field(default_factory=list)


class ProductHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title_parts = []
        self.json_ld_scripts = []
        self.image_candidates = []
        self.option_candidates = []
        self.color_chip_candidates = []
        self._active_title = False
        self._active_json_ld = False
        self._active_option = None
        self._script_parts = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {str(key).lower(): value or '' for key, value in attrs}
        if tag == 'title':
            self._active_title = True
        elif tag == 'script' and 'ld+json' in attrs_dict.get('type', '').lower():
            self._active_json_ld = True
            self._script_parts = []
        elif tag == 'meta':
            key = (attrs_dict.get('property') or attrs_dict.get('name') or '').lower()
            content = attrs_dict.get('content') or ''
            if key and content:
                self.meta[key] = html.unescape(content).strip()
        elif tag == 'img':
            src = attrs_dict.get('src') or attrs_dict.get('data-src') or attrs_dict.get('data-original') or ''
            alt = attrs_dict.get('alt') or ''
            if src:
                self.image_candidates.append({'src': src, 'alt': alt})
        elif tag == 'option':
            self._active_option = []

        style = attrs_dict.get('style', '')
        hex_code = normalize_hex(style)
        label = ' '.join(
            attrs_dict.get(key, '')
            for key in ['aria-label', 'title', 'data-option-name', 'data-value', 'data-name', 'class']
            if attrs_dict.get(key)
        )
        if hex_code and _looks_like_option_context(label):
            self.color_chip_candidates.append({'label': html.unescape(label).strip(), 'hex_code': hex_code})

    def handle_endtag(self, tag):
        if tag == 'title':
            self._active_title = False
        elif tag == 'script' and self._active_json_ld:
            self._active_json_ld = False
            script = ''.join(self._script_parts).strip()
            if script:
                self.json_ld_scripts.append(script)
        elif tag == 'option' and self._active_option is not None:
            text = _clean_text(''.join(self._active_option))
            if text:
                self.option_candidates.append(text)
            self._active_option = None

    def handle_data(self, data):
        if self._active_title:
            self.title_parts.append(data)
        if self._active_json_ld:
            self._script_parts.append(data)
        if self._active_option is not None:
            self._active_option.append(data)


def parse_product_page(html_text, source_url):
    parser = ProductHTMLParser()
    parser.feed(html_text or '')

    json_ld_product = _extract_json_ld_product(parser.json_ld_scripts)
    brand_name = _extract_brand(json_ld_product) or parser.meta.get('product:brand', '')
    product_name = (
        _clean_text(json_ld_product.get('name'))
        or parser.meta.get('og:title', '')
        or parser.meta.get('twitter:title', '')
        or _clean_title(' '.join(parser.title_parts))
    )
    description = (
        _clean_text(json_ld_product.get('description'))
        or parser.meta.get('og:description', '')
        or parser.meta.get('description', '')
    )
    thumbnail_url = (
        _extract_image(json_ld_product)
        or parser.meta.get('og:image', '')
        or parser.meta.get('twitter:image', '')
        or _first_image(parser.image_candidates)
    )

    options = _extract_options(parser, json_ld_product, source_url)
    thumbnail_url = urljoin(source_url, thumbnail_url) if thumbnail_url else ''

    return ParsedProductPage(
        url=source_url,
        brand_name=_clean_text(brand_name),
        product_name=_clean_product_name(product_name),
        description=_clean_text(description),
        thumbnail_url=thumbnail_url,
        options=options,
    )


def _extract_options(parser, json_ld_product, source_url):
    options = []
    seen = set()

    for candidate in parser.color_chip_candidates:
        option = _option_from_text(candidate['label'])
        option.hex_code = candidate['hex_code']
        _append_option(options, seen, option)

    for candidate in parser.option_candidates:
        option = _option_from_text(candidate)
        _append_option(options, seen, option)

    offers = json_ld_product.get('offers') if isinstance(json_ld_product, dict) else None
    if isinstance(offers, list):
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            name = offer.get('name') or offer.get('sku') or ''
            if name:
                _append_option(options, seen, _option_from_text(name))

    image_url = _extract_image(json_ld_product) or _first_image(parser.image_candidates)
    absolute_image_url = urljoin(source_url, image_url) if image_url else ''
    for option in options:
        if not option.image_url:
            option.image_url = absolute_image_url

    if not options:
        options.append(
            ParsedOption(
                option_no='01',
                option_name='대표 색상',
                image_url=absolute_image_url,
            )
        )

    return options[:10]


def _append_option(options, seen, option):
    label = _clean_text(f'{option.option_no} {option.option_name}').lower()
    if not label or label in seen or _is_placeholder_option(label):
        return
    seen.add(label)
    options.append(option)


def _option_from_text(text):
    cleaned = _clean_text(text)
    cleaned = re.sub(r'[\+\-]?\s*[\d,]+\s*원.*$', '', cleaned).strip()
    cleaned = re.sub(r'\([^)]*(품절|sold\s*out|재입고|할인)[^)]*\)', '', cleaned, flags=re.IGNORECASE).strip()
    match = re.search(r'(?:no\.?\s*)?(?P<no>\d{1,3})\s*(?:호|번)?[\s._-]*(?P<name>.+)', cleaned, re.IGNORECASE)
    if match:
        return ParsedOption(
            option_no=match.group('no').zfill(2),
            option_name=_clean_text(match.group('name')),
            hex_code=normalize_hex(cleaned),
        )
    return ParsedOption(option_name=cleaned, hex_code=normalize_hex(cleaned))


def _extract_json_ld_product(scripts):
    for script in scripts:
        try:
            payload = json.loads(html.unescape(script))
        except (TypeError, json.JSONDecodeError):
            continue
        product = _find_product_payload(payload)
        if product:
            return product
    return {}


def _find_product_payload(payload):
    if isinstance(payload, list):
        for item in payload:
            found = _find_product_payload(item)
            if found:
                return found
    if not isinstance(payload, dict):
        return {}

    graph = payload.get('@graph')
    if graph:
        found = _find_product_payload(graph)
        if found:
            return found

    payload_type = payload.get('@type')
    if isinstance(payload_type, list):
        is_product = any(str(item).lower() == 'product' for item in payload_type)
    else:
        is_product = str(payload_type or '').lower() == 'product'
    return payload if is_product else {}


def _extract_brand(product):
    brand = product.get('brand') if isinstance(product, dict) else ''
    if isinstance(brand, dict):
        return brand.get('name') or ''
    return brand or ''


def _extract_image(product):
    image = product.get('image') if isinstance(product, dict) else ''
    if isinstance(image, list):
        return image[0] if image else ''
    if isinstance(image, dict):
        return image.get('url') or image.get('contentUrl') or ''
    return image or ''


def _first_image(images):
    if not images:
        return ''
    preferred = next((image for image in images if _looks_like_product_image(image.get('alt', ''))), None)
    return (preferred or images[0]).get('src', '')


def _looks_like_product_image(text):
    normalized = str(text or '').lower()
    return any(token in normalized for token in ['product', '상품', '제품', '컬러', 'color'])


def _looks_like_option_context(text):
    normalized = str(text or '').lower()
    return any(token in normalized for token in ['option', '옵션', 'color', '컬러', 'shade', '호'])


def _is_placeholder_option(text):
    normalized = str(text or '').lower()
    return any(token in normalized for token in ['선택', '옵션을', '필수', 'choose', 'select', '품절'])


def _clean_product_name(value):
    cleaned = _clean_text(value)
    cleaned = re.split(r'\s[|\-]\s|::', cleaned)[0].strip()
    return cleaned[:160]


def _clean_title(value):
    return _clean_product_name(value)


def _clean_text(value):
    return re.sub(r'\s+', ' ', html.unescape(str(value or ''))).strip()
