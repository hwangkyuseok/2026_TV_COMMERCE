FROM python:3.11-slim

# ── 시스템 패키지 (Playwright chromium 의존성 포함) ───────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        # Playwright chromium 런타임 의존성
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
        libgbm1 libasound2 libpangocairo-1.0-0 libpango-1.0-0 \
        libcairo2 libatspi2.0-0 libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

# ── non-root 사용자 생성 (보안: 컨테이너를 root로 실행하지 않음) ──────────────
RUN groupadd --gid 1001 appuser \
 && useradd  --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# ── Python 의존성 ─────────────────────────────────────────────────────────────
# Build context is project root (set via docker-compose context: .)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Playwright 브라우저 설치 (chromium만) ────────────────────────────────────
# PLAYWRIGHT_BROWSERS_PATH 를 appuser 홈 하위로 지정해 권한 문제를 방지
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.playwright
RUN playwright install chromium \
 && chown -R appuser:appuser /home/appuser/.playwright

# ── 애플리케이션 소스 ─────────────────────────────────────────────────────────
COPY backend/app/ ./app/
COPY mock_data.json ./mock_data.json

# ── 데이터 저장 디렉토리 사전 생성 + 소유권 이전 ─────────────────────────────
RUN mkdir -p /app/HelloVision/log /app/HelloVision/img /app/HelloVision/video \
 && chown -R appuser:appuser /app

# ── 이후 모든 명령은 appuser 권한으로 실행 ───────────────────────────────────
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
