from collections import Counter
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError


class ColorExtractionError(RuntimeError):
    pass


def dominant_color_from_image_url(image_url, *, timeout=8, max_bytes=4_000_000):
    if not image_url:
        raise ColorExtractionError('Image URL is empty.')

    request = Request(
        image_url,
        headers={
            'User-Agent': 'LumiereColorMatcher/1.0',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ColorExtractionError('Image download failed.') from exc

    if len(payload) > max_bytes:
        raise ColorExtractionError('Image is too large.')

    return dominant_color_from_image_bytes(payload)


def dominant_color_from_image_bytes(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert('RGBA')
    except (UnidentifiedImageError, OSError) as exc:
        raise ColorExtractionError('Image format is not supported.') from exc

    image.thumbnail((180, 180))
    pixels = list(image.getdata())
    candidates = []
    for red, green, blue, alpha in pixels:
        if alpha < 32:
            continue
        if _is_background_pixel(red, green, blue):
            continue
        candidates.append((_bucket(red), _bucket(green), _bucket(blue)))

    if not candidates:
        candidates = [(_bucket(red), _bucket(green), _bucket(blue)) for red, green, blue, alpha in pixels if alpha >= 32]
    if not candidates:
        raise ColorExtractionError('No color pixels found.')

    (red, green, blue), _ = Counter(candidates).most_common(1)[0]
    return red, green, blue


def _bucket(value):
    return min(255, max(0, int(round(value / 16)) * 16))


def _is_background_pixel(red, green, blue):
    if red > 235 and green > 235 and blue > 235 and max(red, green, blue) - min(red, green, blue) < 18:
        return True
    if red < 28 and green < 28 and blue < 28:
        return True
    if abs(red - green) < 8 and abs(green - blue) < 8 and red > 205:
        return True
    return False
