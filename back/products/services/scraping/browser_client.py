import logging

from django.conf import settings
from rest_framework import status

from .exceptions import SAFE_SCRAPE_ERROR_MESSAGE, ScrapingError
from .http_client import DEFAULT_USER_AGENT, validate_public_url

logger = logging.getLogger(__name__)


def render_html(url, *, timeout=None):
    safe_url = validate_public_url(url)
    timeout = timeout or int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    logger.info('Rendering product page with Selenium url=%s timeout=%s', safe_url, timeout)

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as exc:
        raise ScrapingError(
            SAFE_SCRAPE_ERROR_MESSAGE,
            code='BROWSER_UNAVAILABLE',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    driver = None
    try:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1365,900')
        options.add_argument('--lang=ko-KR')
        options.add_argument(f'--user-agent={DEFAULT_USER_AGENT}')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(timeout)
        driver.get(safe_url)
        WebDriverWait(driver, timeout).until(
            lambda browser: browser.execute_script('return document.readyState') in {'interactive', 'complete'}
        )
        try:
            WebDriverWait(driver, min(timeout, 5)).until(
                lambda browser: browser.execute_script(
                    'return window.performance && performance.getEntriesByType("resource").length >= 0'
                )
            )
        except Exception:
            logger.info('Selenium network-idle approximation timed out url=%s', safe_url)
        html_text = driver.page_source or ''
        final_url = validate_public_url(driver.current_url or safe_url)
    except Exception as exc:
        logger.exception('Selenium render failed url=%s', safe_url)
        raise ScrapingError(
            SAFE_SCRAPE_ERROR_MESSAGE,
            code='BROWSER_RENDER_FAILED',
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                logger.warning('Failed to close Selenium driver', exc_info=True)

    if not html_text.strip():
        raise ScrapingError(
            SAFE_SCRAPE_ERROR_MESSAGE,
            code='BROWSER_EMPTY_RESPONSE',
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    return html_text, final_url
