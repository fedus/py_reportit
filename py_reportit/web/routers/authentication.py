from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from py_reportit.shared.config.container import Container
from py_reportit.shared.repository.user import UserRepository
from py_reportit.web.schema.token import Token, TokenData
from py_reportit.web.schema.user import User
from py_reportit.web.dependencies import authenticate_user, get_current_active_user, get_session, credentials_exception, create_access_token, create_refresh_token

router = APIRouter(tags=["authentication"], prefix="/auth")

@router.post("/register", status_code=201)
@inject
async def register(
    username = Form(..., description="Username to be registered"),
    password = Form(..., description="Password to be used with new account"),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    session: Session = Depends(get_session)
):
    if user_repository.get_by_username(session, username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username not available",
        )

    new_user = User(username=username, password=password)
    user_repository.create(session, new_user)

@router.post("/token", response_model=Token)
@inject
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = TokenData(username=user.username)

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token, 
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
@inject
async def refresh_token(
    grant_type: str = Form(...),
    refresh_token: str = Form(...),
    config: dict = Depends(Provide[Container.config]),
):
    if grant_type != "refresh_token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(refresh_token, config.get("JWT_SECRET_KEY"), algorithms=[config.get("JWT_ALGORITHM")])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token, 
        token_type="bearer"
    )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
