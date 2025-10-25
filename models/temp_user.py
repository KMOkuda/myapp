from sqlalchemy import Column, BigInteger, String, DateTime, Index
from datetime import datetime
from zoneinfo import ZoneInfo
from settings import Base

JST = ZoneInfo("Asia/Tokyo")

class TempUser(Base):
    __tablename__ = "temp_users"
    __table_args__ = (
        Index("ix_temp_users_email", "email"),
        Index("ix_temp_users_expires_at", "expires_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(JST), nullable=False)

    def __repr__(self):
        return "<TempUser('id={}, name={}, email={}, token={}, expires_at={}')>".format(
            self.id,
            self.name,
            self.email,
            self.token,
            self.expires_at,
        )