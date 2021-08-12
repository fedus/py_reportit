from py_reportit.config.db import db
from py_reportit.config.reportit_api import reportit_api_config
from py_reportit.config.post_processors import post_processors_config

config = { **db, **reportit_api_config, **post_processors_config }
