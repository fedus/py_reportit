import os, sys
from pathlib import Path

from dotenv import dotenv_values

is_dev = "--dev" in sys.argv or os.environ.get("ENV", "PROD") == "DEV"
is_one_off = "--one-off" in sys.argv
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
    "ONE_OFF": is_one_off,
}
