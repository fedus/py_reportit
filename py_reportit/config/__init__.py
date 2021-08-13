import os, sys

from dotenv import dotenv_values

is_dev = "--dev" in sys.argv
dotenv_variant = "dev" if is_dev else "prod"

config = {
    **dotenv_values(f".secrets.{dotenv_variant}.env"),
    **dotenv_values(f".shared.{dotenv_variant}.env"),
    **os.environ,
    "DEV": is_dev,
}
