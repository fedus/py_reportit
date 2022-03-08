from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm.session import Session
from datetime import timedelta
from arrow import Arrow
from jose import JWTError, jwt

from py_reportit.shared.config import config
from py_reportit.shared.model.user import User
from py_reportit.shared.repository.user import UserRepository
from py_reportit.shared.config.container import Container
from py_reportit.web.schema.token import TokenData


# Because oauth_scheme cannot be a function, we cannot use DI in a function
# to generate the tokenUrl and need to explicitly import the config
root_path = config.get("ROOT_PATH", None)
token_url = f"{root_path}/auth/token" if root_path else "/auth/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)

def get_session(request: Request):
    sessionmaker = request.app.container.sessionmaker()
    session = sessionmaker()
    try:
        yield session
    finally:
        session.close()

@inject
def authenticate_user(
    session: Session,
    username: str,
    password: str,
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    user = user_repository.get_by_username(session, username)

    if not user:
        return False
    if not user.password == password:
        return False

    user.last_login = Arrow.now()
    session.commit()

    return user

@inject
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    config: dict = Depends(Provide[Container.config])
):
    to_encode = data.copy()

    if expires_delta:
        expire = Arrow.utcnow() + expires_delta
    else:
        expire = Arrow.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire._datetime})
    encoded_jwt = jwt.encode(to_encode, config.get("JWT_SECRET_KEY"), algorithm=config.get("JWT_ALGORITHM"))

    return encoded_jwt

@inject
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    config: dict = Depends(Provide[Container.config]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.get("JWT_SECRET_KEY"), algorithms=[config.get("JWT_ALGORITHM")])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception

    user = user_repository.get_by_username(session, token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
