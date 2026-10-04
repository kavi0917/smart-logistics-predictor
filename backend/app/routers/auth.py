import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.utils.deps import get_current_user
from app.utils.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger("logistics.auth")


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        logger.warning("Failed login for %s", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = _authenticate(db, body.email, body.password)
    return TokenResponse(access_token=create_access_token(user.email), user_email=user.email, user_name=user.full_name)


@router.post("/token", response_model=TokenResponse, include_in_schema=True)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Form-based login used by the Swagger 'Authorize' button."""
    user = _authenticate(db, form.username, form.password)
    return TokenResponse(access_token=create_access_token(user.email), user_email=user.email, user_name=user.full_name)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
