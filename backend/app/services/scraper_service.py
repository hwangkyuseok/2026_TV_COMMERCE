"""
LG HelloVision 렌탈몰 크롤링 서비스.

전략 (우선순위):
  1순위 — requests + BeautifulSoup HTML 파싱 (실 수집 확인됨)
  2순위 — requests로 REST API GET 호출 (기타 후보 경로)
  3순위 — Playwright (JS 렌더링 필요 시)

  [비활성화 — 코드 보존]
  * AJAX POST API  POST /category/ajax/list.json
  * hotDeal.js CDN 파일 파싱

수집 후:
  - 썸네일 이미지  →  ./HelloVision/img/<상품코드>.webp
  - DB UPSERT      →  TB_PROD_INFO (PostgreSQL)
  [비활성화]
  - 전체 데이터    →  ./HelloVision/sample_data.json  (JSON 파일 저장 중단)
  - PostgreSQL DDL →  ./HelloVision/table_schema.md   (DDL 자동 생성 중단)
"""

import re
import time
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.utils.image_utils import save_image
from app.utils.logger import logger
from app.repositories.product_repository import upsert_hellovision_products

# ── 상수 ──────────────────────────────────────────────────────────────────────
BASE_URL = "https://rental.lghellovision.net"
CDN_BASE_URL = "https://rentalcdn.lghellovision.net"
TIMEOUT = 20
PAGE_SIZE = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": BASE_URL,
    "Origin": BASE_URL,
}

# 네트워크 탭에서 확인된 실제 AJAX 엔드포인트
AJAX_LIST_ENDPOINT = "/category/ajax/list.json"

# CDN에서 직접 내려받는 JS 리소스 (날짜 파라미터는 최신값으로 교체)
from datetime import date as _date
_TODAY_STR = _date.today().strftime("%Y%m%d")
HOTDEAL_JS_URL = f"{CDN_BASE_URL}/resources/biz/hotDeal.js?date={_TODAY_STR}"
CATEGORY_LIST2_JS_URL = f"{BASE_URL}/resources/biz/category/categoryList2.js?date={_TODAY_STR}"

# 기타 REST API GET 후보 경로 (0순위 실패 시 시도)
API_CANDIDATES = [
    "/api/v1/products",
    "/api/products",
    "/api/goods/list",
    "/api/goodsList",
    "/api/item/list",
    "/api/v1/goods/list",
    "/rentalMall/api/goods/list",
    "/shop/api/product/list",
]

# 카테고리 코드 후보
CATEGORY_CODES = ["", "01", "02", "03", "04", "05", "ALL"]


# ── 0순위: AJAX POST API (네트워크 탭으로 확인된 실제 엔드포인트) ──────────────
def _try_ajax_post(session: requests.Session) -> list[dict]:
    """POST /category/ajax/list.json 으로 카테고리별 상품 목록 수집.

    네트워크 탭에서 확인:
      Request URL:  https://rental.lghellovision.net/category/ajax/list.json
      Request Method: POST
      Referrer:     /category/list?hgrnkCtgrSeq=4&subCtgrSeq=12
    """
    url = BASE_URL + AJAX_LIST_ENDPOINT
    products: list[dict] = []
    seen_codes: set[str] = set()

    for cat_name, hgrnk, sub in CATEGORY_LIST:
        referer = f"{BASE_URL}/category/list?hgrnkCtgrSeq={hgrnk}&subCtgrSeq={sub}"
        headers_for_ajax = {**session.headers, "Referer": referer, "X-Requested-With": "XMLHttpRequest"}
        payload = {
            "hgrnkCtgrSeq": hgrnk,
            "subCtgrSeq": sub,
            "pageNo": 1,
            "pageSize": PAGE_SIZE,
        }
        try:
            resp = session.post(url, data=payload, headers=headers_for_ajax, timeout=TIMEOUT)
            if resp.status_code != 200:
                logger.warning(f"AJAX POST 실패 [{cat_name}]: HTTP {resp.status_code}")
                time.sleep(0.5)
                continue

            data = resp.json()
            items = _extract_list_from_json(data)
            added = 0
            for item in items:
                parsed = _parse_json_product(item, cat_name)
                code = parsed.get("product_code", "")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    products.append(parsed)
                    added += 1

            if added:
                logger.info(f"AJAX POST 성공 [{cat_name}]: {added}건")
            else:
                logger.warning(f"AJAX POST 응답 수신했으나 상품 없음 [{cat_name}]")

            time.sleep(0.5)

        except (requests.RequestException, ValueError) as e:
            logger.warning(f"AJAX POST 예외 [{cat_name}]: {e}")
            time.sleep(0.5)

    return products


# ── 0.5순위: hotDeal.js CDN 파일 파싱 ─────────────────────────────────────────
def _try_hotdeal_js(session: requests.Session) -> list[dict]:
    """CDN의 hotDeal.js에서 핫딜 상품 데이터를 파싱.

    CDN URL: https://rentalcdn.lghellovision.net/resources/biz/hotDeal.js
    JS 파일 내부에 var hotDealList = [...] 형태로 데이터가 포함될 것으로 추정.
    """
    products: list[dict] = []
    try:
        resp = session.get(HOTDEAL_JS_URL, timeout=TIMEOUT)
        if resp.status_code != 200:
            logger.warning(f"hotDeal.js 요청 실패: HTTP {resp.status_code}")
            return []

        js_text = resp.text

        # JSON 배열 패턴 추출 (var 변수 = [...] 또는 = {...})
        array_match = re.search(r"=\s*(\[[\s\S]*?\]);", js_text)
        if array_match:
            try:
                items = json.loads(array_match.group(1))
                if isinstance(items, list):
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        parsed = _parse_json_product(item, "핫딜")
                        if not parsed["product_code"]:
                            # seq 없으면 다른 ID 필드 시도
                            for id_key in ("goodsId", "goodsCd", "itemId", "prdtId"):
                                if item.get(id_key):
                                    parsed["product_code"] = str(item[id_key])
                                    break
                        if parsed["product_code"]:
                            parsed["is_hot_deal"] = True
                            products.append(parsed)
                    logger.info(f"hotDeal.js 파싱 성공: {len(products)}건")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"hotDeal.js JSON 파싱 실패: {e}")
        else:
            logger.warning("hotDeal.js에서 JSON 배열 패턴을 찾지 못했습니다.")

    except requests.RequestException as e:
        logger.warning(f"hotDeal.js 요청 예외: {e}")

    return products


# ── 1순위: REST API GET 후보군 ─────────────────────────────────────────────────
def _try_api(session: requests.Session) -> list[dict]:
    """알려진 API 엔드포인트를 순서대로 시도해 상품 목록을 반환."""
    for path in API_CANDIDATES:
        url = BASE_URL + path
        for cat in CATEGORY_CODES:
            params: dict[str, Any] = {"pageNo": 1, "pageSize": PAGE_SIZE}
            if cat:
                params["categoryCode"] = cat
                params["catId"] = cat
            try:
                resp = session.get(url, params=params, timeout=TIMEOUT)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                products = _extract_list_from_json(data)
                if products:
                    logger.info(f"API 호출 성공: {url} (cat={cat or 'ALL'}, {len(products)}건)")
                    return products
            except (requests.RequestException, ValueError):
                pass
    return []


def _extract_list_from_json(data: Any) -> list[dict]:
    """JSON 응답에서 상품 배열을 추출 (다양한 응답 구조 대응)."""
    if isinstance(data, list):
        return data if data and isinstance(data[0], dict) else []

    if isinstance(data, dict):
        for key in ("data", "items", "list", "products", "goods", "result", "content", "bestList"):
            val = data.get(key)
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return val
            if isinstance(val, dict):
                for subkey in ("list", "items", "products", "content"):
                    sub = val.get(subkey)
                    if isinstance(sub, list) and sub and isinstance(sub[0], dict):
                        return sub
    return []


# ── 실제 카테고리 URL 목록 (네트워크 탭 분석으로 확인) ────────────────────────
# 형식: (카테고리명, hgrnkCtgrSeq, subCtgrSeq)
CATEGORY_LIST = [
    ("UHD TV",        2,  3),
    ("LED TV",        2, 68),
    ("냉장고",         3,  5),
    ("김치냉장고",     3,  7),
    ("세탁기",         4, 12),
    ("건조기",         4, 13),
    ("의류관리기",     4, 14),
    ("무선청소기",     4, 49),
    ("로봇청소기",     4, 66),
    ("에어컨",         5, 16),
    ("공기청정기",     5, 17),
    ("냉난방기/선풍기", 5, 20),
    ("정수기",        26,  6),
    ("음식물처리기",  26, 10),
    ("안마의자",       6, 25),
    ("운동기구",       6, 24),
]


# ── JSON 상품 레코드 → 표준 딕셔너리 변환 ────────────────────────────────────
def _parse_json_product(item: dict, category: str = "") -> dict:
    """LG HelloVision JSON 응답 필드 → 표준 상품 딕셔너리 변환.

    주요 필드:
      seq          → product_code
      rpstPrdtNm   → product_name
      brandNm      → brand
      dscnPrcAmt   → monthly_rental_fee (할인 후 금액; 0이면 amtmn 사용)
      imgFileUrl   → thumbnail_url
      subCtgrNm    → category
    """
    seq = str(item.get("seq", ""))
    product_name = item.get("rpstPrdtNm") or item.get("prdtNm", "")
    brand = item.get("brandNm", "")
    monthly_fee = item.get("dscnPrcAmt") or item.get("amtmn", 0)
    thumbnail_url = item.get("imgFileUrl", "")
    cat = item.get("subCtgrNm") or category

    return {
        "product_code": seq,
        "product_name": product_name,
        "brand": brand,
        "monthly_rental_fee": monthly_fee,
        "thumbnail_url": thumbnail_url,
        "detail_url": f"{BASE_URL}/product/detail?seq={seq}" if seq else "",
        "category": cat,
        "scraped_at": datetime.now().isoformat(),
    }


# ── 2순위: HTML 파싱 ───────────────────────────────────────────────────────────
def _try_html(session: requests.Session) -> list[dict]:
    """카테고리 페이지 HTML을 파싱해 상품 카드를 추출.

    LG HelloVision 렌탈몰은 순수 SSR 사이트로, 별도 API 없이
    서버가 HTML에 상품 데이터를 직접 포함해 내려줌.
    상품 카드: <a href="javascript:productClick('섹션명','순번',상품ID)">
    """
    products: list[dict] = []
    seen_codes: set[str] = set()

    for cat_name, hgrnk, sub in CATEGORY_LIST:
        url = f"{BASE_URL}/category/list?hgrnkCtgrSeq={hgrnk}&subCtgrSeq={sub}"
        try:
            resp = session.get(url, timeout=TIMEOUT)
            if resp.status_code != 200:
                logger.warning(f"카테고리 요청 실패 [{cat_name}]: HTTP {resp.status_code}")
                continue

            added = 0

            # ① JSON 응답 먼저 시도 (사이트가 JSON API로 동작하는 경우)
            try:
                data = resp.json()
                items = _extract_list_from_json(data)
                before = len(products)
                for item in items:
                    parsed = _parse_json_product(item, cat_name)
                    code = parsed.get("product_code", "")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        products.append(parsed)
                added = len(products) - before
                if added:
                    logger.info(f"JSON 파싱 성공 [{cat_name}]: {added}건")
            except ValueError:
                pass  # JSON 파싱 실패 → HTML fallback

            # ② HTML 파싱 (JSON에서 상품을 못 찾은 경우)
            if not added:
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("a", href=re.compile(r"productClick"))
                before = len(products)
                for card in cards:
                    item = _parse_card(card, cat_name)
                    code = item.get("product_code", "")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        products.append(item)
                added = len(products) - before
                if added:
                    logger.info(f"HTML 파싱 성공 [{cat_name}]: {added}건")
                else:
                    logger.warning(f"상품 없음 [{cat_name}]: JSON/HTML 모두 실패")

            time.sleep(0.5)  # 서버 부하 방지

        except requests.RequestException as e:
            logger.warning(f"HTML 요청 실패 [{cat_name}]: {e}")

    return products


def _parse_card(card, category: str = "") -> dict:
    """BeautifulSoup <a> Tag → 상품 딕셔너리 변환.

    실제 HTML 구조:
      <a href="javascript:productClick('섹션명','순번',상품ID)">
        <img src="https://rentalcdn.lghellovision.net/...">
        <p>LG 트롬 드럼 세탁기 21kg</p>   ← 상품명
        <p>월34,900원</p>                  ← 월 렌탈료
        <p>16,900원 최저가</p>             ← 최저가(선택)
      </a>
    """
    href = card.get("href", "")

    # 상품 ID: productClick('섹션명', '순번', 상품ID) 의 세 번째 인자
    m = re.search(r"productClick\([^,]+,\s*'[^']*',\s*(\d+)\)", href)
    product_id = m.group(1) if m else ""

    # 이미지
    img_tag = card.find("img")
    thumbnail_url = ""
    if img_tag:
        thumbnail_url = img_tag.get("src") or img_tag.get("data-src") or ""

    # p 태그 목록에서 상품명·가격 추출
    p_tags = card.find_all("p")
    product_name = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else ""
    price_raw    = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else ""

    # 브랜드: 상품명 앞 "[LG]" 또는 "LG " 패턴
    brand = ""
    brand_m = re.match(r"^\[?([A-Za-z가-힣]+)\]?\s", product_name)
    if brand_m:
        brand = brand_m.group(1)

    # 가격: "월34,900원" → 34900
    price_digits = "".join(filter(str.isdigit, price_raw))
    monthly_fee = int(price_digits) if price_digits else 0

    detail_url = f"{BASE_URL}/product/detail?seq={product_id}" if product_id else ""

    return {
        "product_code": product_id,
        "product_name": product_name,
        "brand": brand,
        "monthly_rental_fee": monthly_fee,
        "thumbnail_url": thumbnail_url,
        "detail_url": detail_url,
        "category": category,
        "scraped_at": datetime.now().isoformat(),
    }


# ── 3순위: Playwright (최후 수단) ─────────────────────────────────────────────
def _try_playwright() -> list[dict]:
    """Playwright로 JS 렌더링 후 상품 카드를 추출."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        logger.warning("Playwright가 설치되지 않아 스킵합니다.")
        return []

    # Windows 비(非)메인 스레드에서는 SelectorEventLoop가 기본값이라
    # create_subprocess_exec()이 NotImplementedError를 낸다.
    # ProactorEventLoop로 교체해 Playwright 서브프로세스를 활성화한다.
    import asyncio, sys  # noqa: E401
    if sys.platform == "win32":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    products: list[dict] = []
    logger.info("Playwright로 크롤링 시작…")

    seen_codes: set[str] = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            for cat_name, hgrnk, sub in CATEGORY_LIST[:6]:  # 상위 6개 카테고리만
                url = f"{BASE_URL}/category/list?hgrnkCtgrSeq={hgrnk}&subCtgrSeq={sub}"
                page = browser.new_page()
                page.set_extra_http_headers({"Accept-Language": "ko-KR,ko;q=0.9"})
                try:
                    page.goto(url, wait_until="networkidle", timeout=30_000)
                    page.wait_for_timeout(2_000)
                    soup = BeautifulSoup(page.content(), "html.parser")
                    cards = soup.find_all("a", href=re.compile(r"productClick"))
                    for card in cards:
                        item = _parse_card(card, cat_name)
                        code = item.get("product_code", "")
                        if code and code not in seen_codes:
                            seen_codes.add(code)
                            products.append(item)
                    logger.info(f"Playwright [{cat_name}]: {len(cards)}건")
                except Exception as e:
                    logger.warning(f"Playwright 페이지 오류 [{cat_name}]: {e}")
                finally:
                    page.close()
                time.sleep(0.5)
        finally:
            browser.close()

    return products


# ── 목 데이터 (스크래핑 완전 실패 시 폴백) ────────────────────────────────────
def _mock_products() -> list[dict]:
    """연결 불가 환경에서도 파이프라인 검증용 더미 레코드를 반환."""
    logger.warning("실 데이터 수집 실패 — 목 데이터로 대체합니다.")
    now = datetime.now().isoformat()
    return [
        {
            "product_code": f"HV-MOCK-{i:04d}",
            "product_name": f"[목 데이터] 렌탈 상품 {i}",
            "brand": "LG전자" if i % 2 == 0 else "삼성전자",
            "monthly_rental_fee": 15_000 + i * 2_000,
            "thumbnail_url": "",
            "detail_url": f"{BASE_URL}/product/{i}",
            "category": ["가전", "헬스케어", "IT"][i % 3],
            "scraped_at": now,
        }
        for i in range(1, 11)
    ]


# ── JSON 저장 [비활성화 — DB UPSERT로 대체] ──────────────────────────────────
# def _save_json(products: list[dict]) -> None:
#     ensure_dir(DATA_DIR)
#     out_path = DATA_DIR / "sample_data.json"
#     with open(out_path, "w", encoding="utf-8") as f:
#         json.dump(products, f, ensure_ascii=False, indent=2)
#     logger.info(f"sample_data.json 저장 완료: {out_path} ({len(products)}건)")


# ── PostgreSQL DDL 자동 생성 [비활성화 — TB_PROD_INFO DDL은 document/ddl.sql 참조] ──
# _PY_TO_PG = { ... }
# _COLUMN_COMMENTS = { ... }
# def _infer_pg_type(...): ...
# def _generate_ddl(products): ...


# ── 이미지 일괄 다운로드 ──────────────────────────────────────────────────────
def _download_images(products: list[dict]) -> None:
    save_dir = settings.img_dir / "rental"
    success = 0
    for item in products:
        url = item.get("thumbnail_url", "")
        code = item.get("product_code", "")
        if url and code:
            result = save_image(url, code, save_dir=save_dir)
            if result:
                success += 1
            time.sleep(0.3)  # 서버 부하 방지
    logger.info(f"이미지 다운로드 완료: {success}/{len(products)}건")


# ── 메인 진입점 ───────────────────────────────────────────────────────────────
def run_scrape() -> None:
    """APScheduler에서 30분마다 호출되는 크롤링 작업."""
    started_at = datetime.now()
    logger.info("=" * 60)
    logger.info(f"LG HelloVision 렌탈몰 크롤링 시작  [{started_at:%Y-%m-%d %H:%M:%S}]")
    logger.info("=" * 60)

    session = requests.Session()
    session.headers.update(HEADERS)

    # ① HTML 파싱 (실 수집 확인됨 — 1순위)
    logger.info("[STEP 1/4] HTML 파싱 시도...")
    products = _try_html(session)
    logger.info(f"[STEP 1/4] HTML 파싱 결과: {len(products)}건")

    # ② REST API GET 후보군 (HTML 파싱 실패 시)
    if not products:
        logger.info("[STEP 2/4] HTML 파싱 실패 — REST API GET으로 전환")
        products = _try_api(session)
        logger.info(f"[STEP 2/4] REST API 결과: {len(products)}건")
    else:
        logger.info("[STEP 2/4] HTML 파싱 성공 — REST API 스킵")

    # [비활성화] AJAX POST — 코드 보존, 실행 안 함
    # products = _try_ajax_post(session)

    # [비활성화] hotDeal.js 병합 — 코드 보존, 실행 안 함
    # hotdeal_products = _try_hotdeal_js(session)
    # if hotdeal_products:
    #     existing_codes = {p.get("product_code") for p in products}
    #     new_hotdeal = [p for p in hotdeal_products if p.get("product_code") not in existing_codes]
    #     products.extend(new_hotdeal)
    #     logger.info(f"핫딜 상품 병합: +{len(new_hotdeal)}건")

    # ③ Playwright (HTML·API 모두 실패 시)
    if not products:
        logger.info("[STEP 3/4] HTML·API 모두 실패 — Playwright로 전환")
        try:
            products = _try_playwright()
            logger.info(f"[STEP 3/4] Playwright 결과: {len(products)}건")
        except Exception as e:
            logger.warning(f"[STEP 3/4] Playwright 실패 — 스킵합니다: {e}")
    else:
        logger.info(f"[STEP 3/4] 이미 {len(products)}건 수집됨 — Playwright 스킵")

    # ④ 목 데이터 (완전 실패 시)
    if not products:
        logger.warning("[STEP 3/4] 모든 수집 전략 실패 — 목 데이터로 대체")
        products = _mock_products()

    logger.info(f"수집 완료: 총 {len(products)}건")

    # ── 이미지 다운로드 ────────────────────────────────────────────────────────
    logger.info("[STEP 4/4] 썸네일 이미지 다운로드 시작...")
    _download_images(products)

    # ── DB UPSERT ─────────────────────────────────────────────────────────────
    logger.info("[STEP 4/4] TB_PROD_INFO UPSERT 시작...")
    try:
        affected = upsert_hellovision_products(products)
        logger.info(f"[STEP 4/4] DB UPSERT 성공 — 처리 행 수: {affected}건")
    except Exception as e:
        logger.error(f"[STEP 4/4] DB UPSERT 실패 (크롤링 결과는 보존됨): {e}")

    # ── [비활성화] JSON 파일 저장 — DB UPSERT로 대체 ──────────────────────────
    # existing_path = DATA_DIR / "sample_data.json"
    # if existing_path.exists():
    #     try:
    #         existing = json.loads(existing_path.read_text(encoding="utf-8"))
    #         existing_codes = {p.get("product_code") for p in existing}
    #         new_items = [p for p in products if p.get("product_code") not in existing_codes]
    #         products = existing + new_items
    #         logger.info(f"기존 데이터 병합: +{len(new_items)}건 → 누계 {len(products)}건")
    #     except Exception as e:
    #         logger.warning(f"기존 JSON 병합 실패, 덮어씀: {e}")
    # _save_json(products)

    # ── [비활성화] DDL 자동 생성 — document/ddl.sql 로 대체 ──────────────────
    # _generate_ddl(products)

    elapsed = (datetime.now() - started_at).total_seconds()
    logger.info(f"크롤링 작업 완료 — 소요 시간: {elapsed:.1f}초")
    logger.info("=" * 60)
