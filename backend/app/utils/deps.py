from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Require a valid JWT. Missing/invalid token -> 401 'Authentication required'."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    email = decode_token(token)
    if not email:
        raise unauthorized
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        raise unauthorized
    return user
