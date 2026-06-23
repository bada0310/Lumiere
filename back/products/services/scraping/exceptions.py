from rest_framework import status


SAFE_SCRAPE_ERROR_MESSAGE = 'The URL is unsupported or temporarily inaccessible.'


class ScrapingError(RuntimeError):
    def __init__(
        self,
        message=SAFE_SCRAPE_ERROR_MESSAGE,
        *,
        code='SCRAPE_FAILED',
        status_code=status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.status_code = status_code
        super().__init__(message or SAFE_SCRAPE_ERROR_MESSAGE)
