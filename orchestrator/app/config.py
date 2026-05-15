import os
from pathlib import Path

DB_URL = os.getenv("ORCHESTRATOR_DB_URL", "sqlite:////data/orchestrator.db")
LOGS_DIR = Path(os.getenv("ORCHESTRATOR_LOGS_DIR", "/data/logs"))
DBT_PROJECT_DIR = Path(os.getenv("DBT_PROJECT_DIR", "/dbt"))
DBT_PROFILES_DIR = Path(os.getenv("DBT_PROFILES_DIR", "/dbt"))
DBT_TARGET = os.getenv("DBT_TARGET", "dev")
TIMEZONE = os.getenv("TZ", "America/Sao_Paulo")

LOGS_DIR.mkdir(parents=True, exist_ok=True)
