from fastapi import Request

def get_session(request: Request):
    sessionmaker = request.app.container.sessionmaker()
    session = sessionmaker()
    try:
        yield session
    finally:
        session.close()
