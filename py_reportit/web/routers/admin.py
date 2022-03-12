from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Query, Path, APIRouter
from typing import List, Optional
from datetime import date
from sqlalchemy.orm.session import Session
from enum import Enum

from py_reportit.web.dependencies import get_session, get_current_active_admin
from py_reportit.shared.config.container import Container
from py_reportit.shared.repository.category import CategoryRepository
from py_reportit.shared.model import *


router = APIRouter(tags=["admin"], prefix="/admin", dependencies=[get_current_active_admin])
