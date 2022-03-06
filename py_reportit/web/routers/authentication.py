from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from py_reportit.shared.config.container import Container
from py_reportit.web.schema.token import Token
from py_reportit.web.schema.user import User
from py_reportit.web.dependencies import authenticate_user, create_access_token, get_current_active_user, get_session

router = APIRouter(tags=["authentication"], prefix="/auth")

@router.post("/token", response_model=Token)
@inject
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    config: dict = Depends(Provide[Container.config]),
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(config.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
