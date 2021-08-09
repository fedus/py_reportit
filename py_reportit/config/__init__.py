from py_reportit.config.db import db
from py_reportit.config.reportit_api import reportit_api_config

config = { **db, **reportit_api_config }
