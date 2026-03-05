from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_db
from models import User
from schemas import RegisterIn, TokenOut, MeOut
from auth_utils import hash_password, verify_password, create_access_token, decode_token


router = APIRouter(prefix="/auth", tags=["auth"])

# Swagger будет брать токен отсюда
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------- REGISTER ----------------
@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    user = User(
        email=email,
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email}


# ---------------- LOGIN (OAuth2 form) ----------------
@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.lower()   # Swagger поле username = наш email
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()

    if (not user) or (not verify_password(password, user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    access_token = create_access_token(subject=user.email)

    return TokenOut(access_token=access_token)


# ---------------- GET CURRENT USER ----------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        email = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user


# ---------------- ME ----------------
@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    return MeOut(id=user.id, email=user.email)