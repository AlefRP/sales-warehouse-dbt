from croniter import croniter
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import scheduler as sched
from ..db import get_session
from ..models import Job
from ..runner import trigger_run

templates = Jinja2Templates(directory="orchestrator/app/templates")
router = APIRouter(prefix="/jobs")

VALID_COMMANDS = {"seed", "run", "test", "build", "snapshot", "compile", "source freshness", "deps"}


def _validate(name: str, command: str, cron: str) -> str | None:
    if not name or len(name) > 100:
        return "Nome obrigatório (até 100 caracteres)."
    if command not in VALID_COMMANDS:
        return f"Comando inválido. Use um de: {', '.join(sorted(VALID_COMMANDS))}."
    if not croniter.is_valid(cron):
        return "Expressão cron inválida."
    return None


@router.post("")
def create_job(
    request: Request,
    name: str = Form(...),
    command: str = Form(...),
    selector: str = Form(""),
    cron: str = Form(...),
    is_active: str = Form(None),
    session: Session = Depends(get_session),
):
    err = _validate(name, command, cron)
    if err:
        return templates.TemplateResponse(
            "job_form.html",
            {
                "request": request,
                "job": None,
                "error": err,
            },
            status_code=400,
        )
    if session.query(Job).filter(Job.name == name).first():
        return templates.TemplateResponse(
            "job_form.html",
            {
                "request": request,
                "job": None,
                "error": "Já existe um job com esse nome.",
            },
            status_code=400,
        )
    job = Job(
        name=name.strip(),
        command=command,
        selector=selector.strip() or None,
        cron=cron.strip(),
        is_active=bool(is_active),
    )
    session.add(job)
    session.commit()
    sched.add_or_update(job)
    return RedirectResponse("/jobs", status_code=303)


@router.post("/{job_id}/update")
def update_job(
    job_id: int,
    request: Request,
    name: str = Form(...),
    command: str = Form(...),
    selector: str = Form(""),
    cron: str = Form(...),
    is_active: str = Form(None),
    session: Session = Depends(get_session),
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    err = _validate(name, command, cron)
    if err:
        return templates.TemplateResponse(
            "job_form.html",
            {
                "request": request,
                "job": job,
                "error": err,
            },
            status_code=400,
        )
    job.name = name.strip()
    job.command = command
    job.selector = selector.strip() or None
    job.cron = cron.strip()
    job.is_active = bool(is_active)
    session.commit()
    sched.add_or_update(job)
    return RedirectResponse("/jobs", status_code=303)


@router.post("/{job_id}/delete")
def delete_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    sched.remove(job)
    session.delete(job)
    session.commit()
    return RedirectResponse("/jobs", status_code=303)


@router.post("/{job_id}/toggle")
def toggle_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    job.is_active = not job.is_active
    session.commit()
    sched.add_or_update(job)
    return RedirectResponse("/jobs", status_code=303)


@router.post("/{job_id}/run")
def run_now(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    run_id = trigger_run(job.id, trigger="manual")
    return RedirectResponse(f"/runs/{run_id}", status_code=303)
