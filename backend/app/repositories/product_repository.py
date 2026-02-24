"""
PostgreSQL 연결 및 TB_PROD_INFO UPSERT 레포지토리.

DB 접속 정보 우선순위:
  1순위 — DATABASE_URL  (postgresql://user:pass@host:port/db)
  2순위 — DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD 개별 항목

UPSERT 전략:
  - PLATFORM + PROD_CD 를 Unique Key로 사용 (UK_PLATFORM_PRODUCT_CODE)
  - 기존 행이 있으면 → 변동 가능 컬럼만 UPDATE
  - 없으면            → INSERT
  - psycopg2.extras.execute_values 로 100건 단위 bulk 처리

지원 플랫폼:
  upsert_hellovision_products  — HELLOVISION (IS_RENTAL='Y', IS_AD='N')
  upsert_general_products      — COUPANG / NAVER (IS_RENTAL='N')
"""

from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from app.core.config import settings
from app.utils.logger import logger

# .env 로드 (이미 로드된 경우 재로드하지 않음)
load_dotenv(override=False)

# ── UPSERT SQL ────────────────────────────────────────────────────────────────
# execute_values 는 VALUES %s 를 VALUES (%s,%s,...),(%s,%s,...) 으로 확장합니다.
_UPSERT_SQL = """
INSERT INTO TB_PROD_INFO (
    PLATFORM,
    IS_RENTAL,
    PROD_CD,
    PROD_NM,
    BRAND,
    CATEGORY,
    SALE_PRICE,
    MONTHLY_RENTAL_FEE,
    RENTAL_PERIOD,
    DELIVERY_FEE,
    DELIVERY_TYPE,
    REVIEW_CNT,
    RATING,
    IS_AD,
    THUMBNAIL_URL,
    DETAIL_URL,
    SCRAPED_DT
) VALUES %s
ON CONFLICT (PLATFORM, PROD_CD) DO UPDATE SET
    PROD_NM            = EXCLUDED.PROD_NM,
    BRAND              = EXCLUDED.BRAND,
    CATEGORY           = EXCLUDED.CATEGORY,
    SALE_PRICE         = EXCLUDED.SALE_PRICE,
    MONTHLY_RENTAL_FEE = EXCLUDED.MONTHLY_RENTAL_FEE,
    RENTAL_PERIOD      = EXCLUDED.RENTAL_PERIOD,
    DELIVERY_FEE       = EXCLUDED.DELIVERY_FEE,
    DELIVERY_TYPE      = EXCLUDED.DELIVERY_TYPE,
    REVIEW_CNT         = EXCLUDED.REVIEW_CNT,
    RATING             = EXCLUDED.RATING,
    THUMBNAIL_URL      = EXCLUDED.THUMBNAIL_URL,
    DETAIL_URL         = EXCLUDED.DETAIL_URL,
    SCRAPED_DT         = EXCLUDED.SCRAPED_DT,
    UPDATED_DT         = NOW()
"""

# bulk insert 페이지 크기 (한 번에 DB로 전송하는 행 수)
_BULK_PAGE_SIZE = 100


# ── DB 연결 ───────────────────────────────────────────────────────────────────
def _get_connection() -> psycopg2.extensions.connection:
    """settings에서 접속 정보를 읽어 psycopg2 연결 객체를 반환합니다.

    DATABASE_URL 이 존재하면 우선 사용하고,
    없으면 DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD 를 조합합니다.
    """
    if settings.database_url:
        logger.debug(f"[DB] DATABASE_URL 로 연결: {_mask_url(settings.database_url)}")
        return psycopg2.connect(settings.database_url)

    logger.debug(
        f"[DB] 개별 항목으로 연결: host={settings.db_host} port={settings.db_port} "
        f"db={settings.db_name} user={settings.db_user}"
    )
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def _mask_url(url: str) -> str:
    """로그 출력용 URL 마스킹 (비밀번호 부분을 ***로 대체)."""
    import re
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


# ── 데이터 매핑 ───────────────────────────────────────────────────────────────
def _parse_scraped_dt(raw: str) -> datetime:
    """ISO 8601 문자열 → datetime (파싱 실패 시 현재 시각)."""
    if not raw:
        return datetime.now()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        logger.warning(f"[DB] scraped_at 파싱 실패, 현재 시각으로 대체: '{raw}'")
        return datetime.now()


def _to_db_row(
    product: dict,
    platform: str,
    is_rental: str,
    is_ad: str,
) -> tuple:
    """크롤러 상품 딕셔너리 → TB_PROD_INFO INSERT용 튜플 변환.

    Parameters
    ----------
    product   : 크롤러가 반환한 상품 딕셔너리
    platform  : 'HELLOVISION' | 'COUPANG' | 'NAVER'
    is_rental : 'Y' | 'N'
    is_ad     : 'Y' | 'N'

    Returns
    -------
    _UPSERT_SQL 컬럼 순서와 일치하는 17-tuple
    """
    monthly_fee_raw = product.get("monthly_rental_fee")
    monthly_fee: Optional[int] = int(monthly_fee_raw) if monthly_fee_raw else None

    sale_price_raw = product.get("sale_price")
    sale_price: Optional[int] = int(sale_price_raw) if sale_price_raw else None

    review_cnt_raw = product.get("review_count") or product.get("review_cnt")
    review_cnt: Optional[int] = int(review_cnt_raw) if review_cnt_raw else None

    rating_raw = product.get("rating")
    rating: Optional[float] = float(rating_raw) if rating_raw else None

    delivery_fee_raw = product.get("delivery_fee")
    delivery_fee: int = int(delivery_fee_raw) if delivery_fee_raw is not None else 0

    rental_period_raw = product.get("rental_period")
    rental_period: Optional[int] = int(rental_period_raw) if rental_period_raw else None

    scraped_dt = _parse_scraped_dt(product.get("scraped_at", ""))

    return (
        platform,                                      # PLATFORM
        is_rental,                                     # IS_RENTAL
        str(product.get("product_code", "")),          # PROD_CD
        str(product.get("product_name", "")),          # PROD_NM
        product.get("brand") or None,                  # BRAND
        product.get("category") or None,               # CATEGORY
        sale_price,                                    # SALE_PRICE
        monthly_fee,                                   # MONTHLY_RENTAL_FEE
        rental_period,                                 # RENTAL_PERIOD
        delivery_fee,                                  # DELIVERY_FEE
        product.get("delivery_type") or None,          # DELIVERY_TYPE
        review_cnt,                                    # REVIEW_CNT
        rating,                                        # RATING
        is_ad,                                         # IS_AD
        product.get("thumbnail_url") or None,          # THUMBNAIL_URL
        product.get("detail_url") or None,             # DETAIL_URL
        scraped_dt,                                    # SCRAPED_DT
    )


# ── 공통 UPSERT 실행 ──────────────────────────────────────────────────────────
def _execute_upsert(rows: list[tuple], platform: str) -> int:
    """rows 를 TB_PROD_INFO에 bulk UPSERT하고 처리 행 수를 반환합니다.

    try-except-finally 구조로 DB 연결이 항상 안전하게 닫힙니다.
    """
    conn: Optional[psycopg2.extensions.connection] = None
    cursor: Optional[psycopg2.extensions.cursor] = None

    try:
        logger.debug(f"[DB:{platform}] DB 연결 시도...")
        conn = _get_connection()
        cursor = conn.cursor()
        logger.info(f"[DB:{platform}] DB 연결 성공 (PID={conn.get_backend_pid()})")

        logger.info(f"[DB:{platform}] execute_values 실행 — {len(rows)}건 / page_size={_BULK_PAGE_SIZE}")
        psycopg2.extras.execute_values(cursor, _UPSERT_SQL, rows, page_size=_BULK_PAGE_SIZE)

        affected = cursor.rowcount
        conn.commit()

        logger.info(
            f"[DB:{platform}] UPSERT 완료 ✓ "
            f"— 입력={len(rows)}건, 처리(rowcount)={affected}건"
        )
        return affected

    except psycopg2.OperationalError as e:
        logger.error(f"[DB:{platform}] DB 연결 실패: {e}")
        if conn:
            conn.rollback()
            logger.warning(f"[DB:{platform}] 트랜잭션 롤백 완료")
        raise

    except psycopg2.Error as e:
        logger.error(f"[DB:{platform}] UPSERT 실패 (psycopg2.Error): {e}")
        if conn:
            conn.rollback()
            logger.warning(f"[DB:{platform}] 트랜잭션 롤백 완료")
        raise

    except Exception as e:
        logger.error(f"[DB:{platform}] 예기치 않은 오류: {e}")
        if conn:
            conn.rollback()
            logger.warning(f"[DB:{platform}] 트랜잭션 롤백 완료")
        raise

    finally:
        if cursor:
            cursor.close()
            logger.debug(f"[DB:{platform}] 커서 닫힘")
        if conn and not conn.closed:
            conn.close()
            logger.debug(f"[DB:{platform}] DB 연결 닫힘")


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────
def upsert_hellovision_products(products: list[dict]) -> int:
    """LG HelloVision 렌탈 상품 목록을 TB_PROD_INFO에 UPSERT합니다.

    고정 매핑:
      PLATFORM  = 'HELLOVISION'
      IS_RENTAL = 'Y'
      IS_AD     = 'N'

    Parameters
    ----------
    products : 크롤러가 반환한 상품 딕셔너리 리스트

    Returns
    -------
    처리된 행 수 (rowcount)
    """
    platform = "HELLOVISION"

    if not products:
        logger.warning(f"[DB:{platform}] UPSERT 대상 데이터 없음 — 스킵")
        return 0

    logger.info(f"[DB:{platform}] UPSERT 준비 시작 — 입력 {len(products)}건")

    # 유효한 product_code 를 가진 항목만 처리
    valid = [p for p in products if p.get("product_code")]
    skipped = len(products) - len(valid)
    if skipped:
        logger.warning(f"[DB:{platform}] product_code 없는 항목 제외: {skipped}건")

    if not valid:
        logger.error(f"[DB:{platform}] 유효한 상품 없음 — UPSERT 중단")
        return 0

    # 딕셔너리 → DB 튜플 변환 (단계별 로깅)
    logger.debug(f"[DB:{platform}] 데이터 변환 시작 ({len(valid)}건)")
    rows: list[tuple] = []
    for idx, product in enumerate(valid, start=1):
        row = _to_db_row(product, platform, is_rental="Y", is_ad="N")
        rows.append(row)
        if idx % 50 == 0 or idx == len(valid):
            logger.debug(f"[DB:{platform}] 변환 진행: {idx}/{len(valid)}건")

    logger.info(f"[DB:{platform}] 데이터 변환 완료 — {len(rows)}건 → DB 전송 시작")
    return _execute_upsert(rows, platform)


def upsert_general_products(products: list[dict], platform: str) -> int:
    """쿠팡 / 네이버 등 일반 판매 상품을 TB_PROD_INFO에 UPSERT합니다.

    고정 매핑:
      IS_RENTAL = 'N'
      IS_AD     = 각 상품의 'is_ad' 필드 (기본 'N')

    Parameters
    ----------
    products : 크롤러가 반환한 상품 딕셔너리 리스트
    platform : 'COUPANG' | 'NAVER'

    Returns
    -------
    처리된 행 수 (rowcount)
    """
    platform = platform.upper()
    allowed = {"COUPANG", "NAVER"}
    if platform not in allowed:
        logger.error(f"[DB:{platform}] 지원하지 않는 플랫폼: {platform}. 허용: {allowed}")
        return 0

    if not products:
        logger.warning(f"[DB:{platform}] UPSERT 대상 데이터 없음 — 스킵")
        return 0

    logger.info(f"[DB:{platform}] UPSERT 준비 시작 — 입력 {len(products)}건")

    valid = [p for p in products if p.get("product_code")]
    skipped = len(products) - len(valid)
    if skipped:
        logger.warning(f"[DB:{platform}] product_code 없는 항목 제외: {skipped}건")

    if not valid:
        logger.error(f"[DB:{platform}] 유효한 상품 없음 — UPSERT 중단")
        return 0

    logger.debug(f"[DB:{platform}] 데이터 변환 시작 ({len(valid)}건)")
    rows: list[tuple] = []
    for idx, product in enumerate(valid, start=1):
        # IS_AD: 상품에 is_ad 플래그가 있으면 사용, 없으면 'N'
        is_ad = "Y" if product.get("is_ad") else "N"
        row = _to_db_row(product, platform, is_rental="N", is_ad=is_ad)
        rows.append(row)
        if idx % 50 == 0 or idx == len(valid):
            logger.debug(f"[DB:{platform}] 변환 진행: {idx}/{len(valid)}건")

    logger.info(f"[DB:{platform}] 데이터 변환 완료 — {len(rows)}건 → DB 전송 시작")
    return _execute_upsert(rows, platform)
