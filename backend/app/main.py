"""TV Commerce 백엔드 — FastAPI 앱 진입점.

이 파일의 역할:
  1. FastAPI 앱 인스턴스 생성 및 미들웨어 설정
  2. lifespan 이벤트로 스케줄러 시작/종료 위임
  3. 라우터 등록

비즈니스 로직(크롤링, 스케줄 잡 등록 등)은 각 서비스/코어 모듈에서 담당합니다.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import mock_api
from app.core.config import settings
from app.core.scheduler import create_and_start_scheduler
from app.utils.logger import logger


# ── Lifespan: 앱 기동·종료 시 실행 ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler = create_and_start_scheduler()
    yield
    scheduler.shutdown(wait=False)
    logger.info("APScheduler 종료")


# ── FastAPI 앱 ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TV Commerce Mock API",
    description="Smart TV Commerce Platform — Mock Data API + HelloVision Scraper",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS: settings.cors_origins (기본값: "*" 전체 허용)
# 예) CORS_ORIGINS=http://<서버IP>:3000,https://yourdomain.com
_allow_origins = (
    [o.strip() for o in settings.cors_origins.split(",")]
    if settings.cors_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_api.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
