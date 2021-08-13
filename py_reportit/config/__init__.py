import os

from dotenv import dotenv_values

config = {
    **dotenv_values(".secrets.dev.env"),
    **dotenv_values(".shared.dev.env"),
    **os.environ,
}
