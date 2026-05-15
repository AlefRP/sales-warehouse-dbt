import os
import shlex
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from .config import DBT_PROFILES_DIR, DBT_PROJECT_DIR, DBT_TARGET, LOGS_DIR
from .db import SessionLocal
from .models import Job, Run


def _build_command(job: Job) -> list[str]:
    cmd = [
        "dbt",
        job.command,
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--target",
        DBT_TARGET,
    ]
    if job.selector:
        cmd.extend(shlex.split(job.selector))
    return cmd


def _execute(run_id: int, job_id: int) -> None:
    session = SessionLocal()
    try:
        run = session.get(Run, run_id)
        job = session.get(Job, job_id)
        if run is None or job is None:
            return

        cmd = _build_command(job)
        run.command_line = " ".join(cmd)
        log_path = LOGS_DIR / f"run_{run.id}.log"
        run.log_path = str(log_path)
        session.commit()

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"$ {run.command_line}\n\n")
            f.flush()
            # Desliga códigos ANSI de cor — o log vai pra arquivo/HTML, não TTY.
            env = os.environ.copy()
            env["NO_COLOR"] = "1"
            env["DBT_USE_COLORS"] = "False"
            proc = subprocess.Popen(
                cmd,
                cwd=str(DBT_PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
            for line in proc.stdout:
                f.write(line)
                f.flush()
            proc.wait()

        run.return_code = proc.returncode
        run.status = "success" if proc.returncode == 0 else "failed"
        run.finished_at = datetime.utcnow()
        run.duration_seconds = int((run.finished_at - run.started_at).total_seconds())
        session.commit()
    except Exception as exc:  # noqa: BLE001
        run = session.get(Run, run_id)
        if run is not None:
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.duration_seconds = int((run.finished_at - run.started_at).total_seconds())
            log_path = Path(run.log_path) if run.log_path else LOGS_DIR / f"run_{run.id}.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[orchestrator error] {exc}\n")
            session.commit()
    finally:
        session.close()


def trigger_run(job_id: int, trigger: str = "scheduled") -> int:
    """Cria um Run no DB e dispara a execução em thread separada."""
    session = SessionLocal()
    try:
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} não encontrado")
        run = Run(job_id=job.id, trigger=trigger, status="running", started_at=datetime.utcnow())
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()

    thread = threading.Thread(target=_execute, args=(run_id, job_id), daemon=True)
    thread.start()
    return run_id
