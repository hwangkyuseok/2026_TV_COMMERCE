"""
이미지 유틸리티 모듈.
- ensure_dir  : pathlib로 폴더가 없으면 자동 생성
- save_image  : URL에서 이미지를 내려받아 최대 500px 리사이즈 후 WebP(품질 80%)로 저장

경로 결정 원칙:
  save_dir 인자를 항상 명시적으로 전달하세요.
  예) save_image(url, code, save_dir=settings.img_dir / "rental")
  생략 시 settings.img_dir 를 기본값으로 사용합니다.
"""

import io
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

from app.core.config import settings
from app.utils.logger import logger

_REQUEST_TIMEOUT = 15  # 초


def ensure_dir(path: Path) -> Path:
    """경로가 없으면 자동 생성 후 반환."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(url: str, product_code: str, save_dir: Optional[Path] = None) -> Optional[Path]:
    """
    이미지를 URL에서 다운로드하여 WebP 포맷으로 압축 저장.

    Parameters
    ----------
    url          : 다운로드할 이미지 URL
    product_code : 저장 파일명으로 사용할 상품코드
    save_dir     : 저장 디렉토리 (기본값: settings.img_dir)
                   플랫폼별 하위 경로를 명시적으로 전달하는 것을 권장합니다.
                   예) settings.img_dir / "rental"
                       settings.img_dir / "coupang"

    Returns
    -------
    저장된 파일 경로, 실패 시 None
    """
    # save_dir 미전달 시 settings.img_dir 를 기본값으로 사용
    target_dir = Path(save_dir) if save_dir is not None else settings.img_dir

    # 저장 전 부모 디렉토리 자동 생성 (누락 시도 방지)
    target_dir.mkdir(parents=True, exist_ok=True)

    save_path = target_dir / f"{product_code}.webp"

    # 이미 저장된 파일이면 재다운로드 생략
    if save_path.exists():
        logger.debug(f"이미지 이미 존재, 스킵: {save_path.name}")
        return save_path

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        # 팔레트 모드(P)에 바이트 투명도가 있으면 RGBA 경유 후 RGB 변환
        # 직접 RGB 변환 시 PIL UserWarning + 투명 픽셀이 검정으로 손실됨
        if img.mode == "P":
            img = img.convert("RGBA")
        img = img.convert("RGB")

        # 최대 500px 리사이즈 (비율 유지)
        img.thumbnail((500, 500), Image.LANCZOS)

        # WebP 저장 (품질 80%)
        img.save(save_path, format="WEBP", quality=80, method=4)
        logger.debug(f"이미지 저장 완료: {save_path} ({img.size})")
        return save_path

    except requests.RequestException as e:
        logger.warning(f"이미지 다운로드 실패 [{product_code}]: {e}")
    except Exception as e:
        logger.error(f"이미지 처리 오류 [{product_code}]: {e}")

    return None
