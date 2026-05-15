import contextlib

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import TIMEZONE
from .db import SessionLocal
from .models import Job
from .runner import trigger_run

scheduler = BackgroundScheduler(timezone=TIMEZONE)


def _job_id(job: Job) -> str:
    return f"job-{job.id}"


def add_or_update(job: Job) -> None:
    if not job.is_active:
        remove(job)
        return
    scheduler.add_job(
        trigger_run,
        CronTrigger.from_crontab(job.cron, timezone=TIMEZONE),
        id=_job_id(job),
        args=[job.id, "scheduled"],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def remove(job: Job) -> None:
    with contextlib.suppress(Exception):
        scheduler.remove_job(_job_id(job))


def next_run_time(job: Job):
    try:
        sj = scheduler.get_job(_job_id(job))
        return sj.next_run_time if sj else None
    except Exception:  # noqa: BLE001
        return None


def start():
    if scheduler.running:
        return
    scheduler.start()
    session = SessionLocal()
    try:
        for job in session.query(Job).all():
            if job.is_active:
                add_or_update(job)
    finally:
        session.close()


def shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)
