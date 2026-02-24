"""APScheduler 설정 — 주기적 크롤링 작업 관리.

새로운 스케줄 작업이 생기면 이 파일에 add_job() 만 추가하면 되며,
main.py 를 건드릴 필요가 없습니다.
"""

from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone as pytz_timezone

from app.services.scraper_service import run_scrape
from app.utils.logger import logger

_KST = pytz_timezone("Asia/Seoul")


def _register_jobs(scheduler: BackgroundScheduler) -> None:
    """스케줄러에 실행 잡(Job)을 등록합니다.

    서비스가 늘어나면 이 함수 안에 add_job() 블록을 추가하세요.
    """
    # ── LG HelloVision 렌탈몰 크롤링 (30분 간격) ─────────────────────────────
    # next_run_time 을 30초 후로 설정: 서버가 완전히 기동된 후 크롤링 시작.
    # (즉시 실행 시 uvicorn --reload 재시작 오버헤드와 겹쳐 요청 실패 가능)
    scheduler.add_job(
        run_scrape,
        trigger="interval",
        minutes=30,
        id="hellovision_scraper",
        name="LG HelloVision 렌탈몰 크롤링",
        max_instances=1,                                    # 동시 중복 실행 방지
        coalesce=True,                                      # 밀린 잡은 1회만 실행
        misfire_grace_time=60,                             # 60초 이내 지연은 허용
        next_run_time=datetime.now(_KST) + timedelta(seconds=30),  # 30초 후 첫 실행
    )

    # ── 추후 서비스 추가 예시 ──────────────────────────────────────────────────
    # scheduler.add_job(
    #     run_another_service,
    #     trigger="interval",
    #     hours=1,
    #     id="another_service",
    #     name="다른 서비스 설명",
    #     max_instances=1,
    #     next_run_time=datetime.now(_KST),
    # )


def create_and_start_scheduler() -> BackgroundScheduler:
    """잡이 등록된 스케줄러를 생성·시작하고 반환합니다.

    lifespan 컨텍스트에서 호출하세요.
    종료 시에는 반환된 객체로 scheduler.shutdown() 을 호출하면 됩니다.
    """
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    _register_jobs(scheduler)
    scheduler.start()
    logger.info("APScheduler 시작 — 등록된 잡 목록:")
    for job in scheduler.get_jobs():
        logger.info(f"  · [{job.id}] {job.name} | 다음 실행: {job.next_run_time}")

    return scheduler
