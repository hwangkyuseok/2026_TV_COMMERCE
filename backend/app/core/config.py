"""
애플리케이션 설정 — 환경변수 중앙 관리.

우선순위: 환경변수 > .env 파일 > 기본값
pydantic-settings BaseSettings 가 타입 변환·검증을 처리합니다.

경로 조립은 이 파일에 집중시키고, 서비스 로직은 settings.xxx_dir 을 호출만 합니다.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── CORS ──────────────────────────────────────────────────────────────────
    # 콤마 구분 도메인 또는 "*" (전체 허용)
    # 예) CORS_ORIGINS=http://ip:3000,https://yourdomain.com
    cors_origins: str = "*"

    # ── PostgreSQL ─────────────────────────────────────────────────────────────
    # DATABASE_URL 이 .env 에 정의되어 있으면 최우선 사용.
    # 없을 경우 resolved_database_url property 가 개별 항목을 조합합니다.
    database_url: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    # ── 데이터 저장 루트 경로 ──────────────────────────────────────────────────
    # 로컬 기본값: ./HelloVision  (uvicorn 실행 디렉토리 기준 상대경로)
    # Docker   : /app/HelloVision (docker-compose environment 로 주입)
    hellovision_data_dir: str = "./HelloVision"

    # ── .env 인식 설정 ─────────────────────────────────────────────────────────
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",          # 불필요한 환경변수로 인한 경고 억제
    }

    # ── DB URL 조립 ───────────────────────────────────────────────────────────
    @property
    def resolved_database_url(self) -> str:
        """
        DATABASE_URL 이 .env 에 있으면 그대로 반환.
        없으면 개별 항목(host / port / name / user / password)을 조합.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── 경로 Property (pathlib.Path 기반, OS 간 호환) ─────────────────────────
    @property
    def data_dir(self) -> Path:
        """데이터 저장 루트 디렉토리."""
        return Path(self.hellovision_data_dir)

    @property
    def img_dir(self) -> Path:
        """이미지 저장 디렉토리 (플랫폼별 하위 경로로 확장 가능)."""
        return self.data_dir / "img"

    @property
    def log_dir(self) -> Path:
        """로그 저장 디렉토리."""
        return self.data_dir / "log"

    @property
    def video_dir(self) -> Path:
        """영상 저장 디렉토리."""
        return self.data_dir / "video"


settings = Settings()
