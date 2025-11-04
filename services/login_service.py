from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from deps import verify_password
from models.user import User 

class LoginService:
    """ログイン認証サービス"""

    def __init__(self, db: Session):
        self.db = db

    def login(self, email: str, password: str) -> Optional[User]:
        """メールとパスワードでユーザー認証。成功なら User、失敗なら None"""
        user: Optional[User] = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user