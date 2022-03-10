import os, sys
import requests_random_user_agent

from pathlib import Path
from dotenv import dotenv_values

is_dev = "--dev" in sys.argv or os.environ.get("ENV", "PROD") == "DEV"

special_run_mode = "ONE_OFF_CRAWL" if "--one-off-crawl" in sys.argv else (
    "ONE_OFF_PP" if "--one-off-pp" in sys.argv else (
        "RESUME" if "--resume" in sys.argv else None
    )
)

dotenv_variant = "dev" if is_dev else "prod"

base_path = Path(os.environ.get('PY_REPORTIT_CONFIG_DIR', '.'))

config = {
    **dotenv_values(f"{base_path}/.secrets.base.env"),
    **dotenv_values(f"{base_path}/.shared.base.env"),
    **dotenv_values(f"{base_path}/.secrets.{dotenv_variant}.env"),
    **dotenv_values(f"{base_path}/.shared.{dotenv_variant}.env"),
    **dotenv_values(f"{base_path}/.secrets.local.env"),
    **dotenv_values(f"{base_path}/.shared.local.env"),
    **os.environ,
    "DEV": is_dev,
    "SPECIAL_RUN_MODE": special_run_mode,
}
