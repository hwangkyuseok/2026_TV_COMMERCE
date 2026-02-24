"""
loguru 기반 로거 설정.
- 일자별 파일 분리: HelloVision/log/hellovision_YYYY-MM-DD.log  (자정마다 rotate)
- 용량별 파일 분리: HelloVision/log/hellovision_size_*.log     (10 MB마다 rotate)
- 30일 보관 후 zip 압축
"""

import sys
from pathlib import Path

from loguru import logger  # noqa: F401  (re-export)

from app.core.config import settings

# ── 로그 디렉토리 자동 생성 ────────────────────────────────────────────────────
LOG_DIR = Path(settings.hellovision_data_dir) / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── 기본 핸들러 제거 ──────────────────────────────────────────────────────────
logger.remove()

# ── 콘솔 출력 (INFO 이상) ─────────────────────────────────────────────────────
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
)

# ── 파일 출력 ① : 일자별 rotate (매일 자정) ───────────────────────────────────
logger.add(
    str(LOG_DIR / "hellovision_{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    rotation="00:00",       # 매일 자정에 새 파일 생성
    retention="30 days",    # 30일 경과 파일 삭제
    compression="zip",      # 오래된 파일 zip 압축
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
)

# ── 파일 출력 ② : 용량별 rotate (10 MB 초과) ─────────────────────────────────
logger.add(
    str(LOG_DIR / "hellovision_size_{time}.log"),
    level="DEBUG",
    rotation="10 MB",       # 10 MB 초과 시 새 파일 생성
    retention="10 days",
    compression="zip",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
)

__all__ = ["logger"]
