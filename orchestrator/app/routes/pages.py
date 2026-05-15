from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .. import scheduler as sched
from ..db import get_session
from ..models import Job, Run

templates = Jinja2Templates(directory="orchestrator/app/templates")
router = APIRouter()


def _stats(session: Session) -> dict:
    total_jobs = session.query(Job).count()
    active_jobs = session.query(Job).filter(Job.is_active.is_(True)).count()
    total_runs = session.query(Run).count()
    success = session.query(Run).filter(Run.status == "success").count()
    failed = session.query(Run).filter(Run.status == "failed").count()
    running = session.query(Run).filter(Run.status == "running").count()
    rate = (success / total_runs * 100) if total_runs else None
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_runs": total_runs,
        "success": success,
        "failed": failed,
        "running": running,
        "success_rate": rate,
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    stats = _stats(session)
    recent = session.query(Run).order_by(desc(Run.started_at)).limit(15).all()
    jobs = session.query(Job).order_by(Job.name).all()
    next_runs = [(j, sched.next_run_time(j)) for j in jobs if j.is_active]
    next_runs = sorted([n for n in next_runs if n[1]], key=lambda x: x[1])[:5]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "recent": recent,
            "next_runs": next_runs,
        },
    )


@router.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request, session: Session = Depends(get_session)):
    jobs = session.query(Job).order_by(Job.name).all()
    next_map = {j.id: sched.next_run_time(j) for j in jobs}
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "next_map": next_map,
        },
    )


@router.get("/jobs/new", response_class=HTMLResponse)
def new_job(request: Request):
    return templates.TemplateResponse(
        "job_form.html",
        {
            "request": request,
            "job": None,
            "error": None,
        },
    )


@router.get("/jobs/{job_id}/edit", response_class=HTMLResponse)
def edit_job(job_id: int, request: Request, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    return templates.TemplateResponse(
        "job_form.html",
        {
            "request": request,
            "job": job,
            "error": None,
        },
    )


@router.get("/runs", response_class=HTMLResponse)
def runs_page(request: Request, session: Session = Depends(get_session)):
    runs = session.query(Run).order_by(desc(Run.started_at)).limit(100).all()
    return templates.TemplateResponse("runs.html", {"request": request, "runs": runs})


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(run_id: int, request: Request, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(404)
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run})


@router.get("/runs/{run_id}/log", response_class=HTMLResponse)
def run_log_partial(run_id: int, request: Request, session: Session = Depends(get_session)):
    """Fragment HTMX com o log atual + auto-refresh enquanto rodando."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(404)
    log = ""
    if run.log_path and Path(run.log_path).exists():
        log = Path(run.log_path).read_text(encoding="utf-8", errors="replace")
    response = templates.TemplateResponse(
        "_run_log.html",
        {
            "request": request,
            "run": run,
            "log": log,
        },
    )
    # HTTP 286 é o código sentinela do htmx para "Stop Polling".
    # Quando a run termina, devolvemos 286 para encerrar o intervalo no cliente.
    if run.status != "running":
        response.status_code = 286
    return response


@router.get("/runs/{run_id}/log.txt", response_class=PlainTextResponse)
def run_log_raw(run_id: int, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run or not run.log_path or not Path(run.log_path).exists():
        raise HTTPException(404)
    return Path(run.log_path).read_text(encoding="utf-8", errors="replace")
