import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt  # Ensure this is from python-jose
from passlib.context import CryptContext # type: ignore
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables from .env file

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)

def get_password_hash(password):
    logger.info("Hashing password")
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    logger.info("Verifying password")
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    logger.info("Creating access token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("Access token created")
    return encoded_jwt

def verify_token(token: str):
    logger.info("Verifying token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Token verification failed: username is None")
            return None
        logger.info("Token verified successfully")
        return username
    except JWTError:
        logger.error("Token verification failed: JWTError")
        return None
