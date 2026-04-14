from pwdlib import PasswordHash
from app.models import *
from app.database import get_session
from sqlmodel import select
from datetime import timedelta, datetime, timezone
from app.database import SessionDep
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException, status, Request, APIRouter
import jwt
from jwt.exceptions import InvalidTokenError

SECRET_KEY = "ThisIsAnExampleOfWhatNotToUseAsTheSecretKeyIRL"
ALGORITHM = "HS256"

auth_router = APIRouter(tags=["Authentication"])

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Converts plaintext password to encrypted password
def encrypt_password(password:str):
    return password_hash.hash(password)

# Verifies if a plaintext password, when encrypted, gives the same output as the expected encrypted password
def verify_password(plaintext_password:str, encrypted_password):
    return password_hash.verify(password=plaintext_password, hash=encrypted_password)

# This takes some information and converts it into a JWT
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = db.exec(select(RegularUser).where(RegularUser.username == form_data.username)).one_or_none()
    if not user or not verify_password(plaintext_password=form_data.password, encrypted_password=user.password):
        user = db.exec(select(Admin).where(Admin.username == form_data.username)).one_or_none()
        if not user or not verify_password(plaintext_password=form_data.password, encrypted_password=user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return Token(access_token=access_token, token_type="bearer")

@auth_router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup_user(user_data: UserCreate, db: SessionDep):
    try:
        new_user = RegularUser(
            username=user_data.username, 
            email=user_data.email, 
            password=encrypt_password(user_data.password)
        )
        db.add(new_user)
        db.commit()
        return new_user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

@auth_router.get("/identify", response_model=UserResponse)
def get_user_by_id(db: SessionDep, user: AuthDep):
    return user

async def get_current_user(request: Request, db: SessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    auth_header = request.headers.get("Authorization")
    
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub", None)
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = db.get(RegularUser, int(user_id))
    if not user:
        user = db.get(Admin, int(user_id))
        
    if user is None:
        raise credentials_exception
    return user


AuthDep = Annotated[User, Depends(get_current_user)]