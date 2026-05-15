from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import scheduler as sched
from .db import init_db
from .routes import jobs, pages


def _fmt_dt(value):
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _fmt_duration(seconds):
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    sched.start()
    yield
    sched.shutdown()


app = FastAPI(title="postgres_dbt orchestrator", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="orchestrator/static"), name="static")
app.include_router(pages.router)
app.include_router(jobs.router)

for tpl in (pages.templates, jobs.templates):
    tpl.env.filters["fmt_dt"] = _fmt_dt
    tpl.env.filters["fmt_duration"] = _fmt_duration


@app.get("/healthz")
def healthz():
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}
