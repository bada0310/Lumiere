from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScrapedColorOption(BaseModel):
    model_config = ConfigDict(extra='ignore')

    option_name: str = ''
    color_code: str | None = None
    image_url: str | None = None

    @field_validator('option_name', mode='before')
    @classmethod
    def normalize_option_name(cls, value):
        return str(value or '').strip()

    @field_validator('color_code', mode='before')
    @classmethod
    def normalize_color_code(cls, value):
        text = str(value or '').strip()
        return text or None

    @field_validator('image_url', mode='before')
    @classmethod
    def normalize_image_url(cls, value):
        text = str(value or '').strip()
        return text or None


class ScrapedProduct(BaseModel):
    model_config = ConfigDict(extra='ignore')

    product_name: str = ''
    brand: str = ''
    options: list[ScrapedColorOption] = Field(default_factory=list)
    source: str = ''
    product_url: str = ''
    final_url: str = ''
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('product_name', 'brand', 'source', 'product_url', 'final_url', mode='before')
    @classmethod
    def normalize_text(cls, value):
        return str(value or '').strip()

    def public_payload(self):
        return {
            'product_name': self.product_name,
            'brand': self.brand,
            'options': [option.model_dump() for option in self.options],
        }
