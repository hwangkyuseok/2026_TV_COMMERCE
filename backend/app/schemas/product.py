"""
TB_PROD_INFO 기반 상품 Pydantic 스키마.
API 응답 직렬화 및 레이어 간 데이터 계약으로 사용합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductSchema(BaseModel):
    product_code: str
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    sale_price: Optional[int] = None
    monthly_rental_fee: Optional[int] = None
    rental_period: Optional[int] = None
    delivery_fee: int = 0
    delivery_type: Optional[str] = None
    review_cnt: Optional[int] = None
    rating: Optional[float] = None
    thumbnail_url: Optional[str] = None
    detail_url: Optional[str] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}
