from sqlalchemy.orm import Session
from settings import Engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_db():
    db = Session(Engine)
    try:
        yield db
    finally:
        db.close()

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)