from sqlalchemy import Column, BigInteger, String, DateTime, func

from settings import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


    def __repr__(self):
        return "<User('id={}, name={}', password_hash={}, email={}, created_at={}, updated_at={})>".format(
            self.id,
            self.name,
            self.password_hash,
            self.email,
            self.created_at,
            self.updated_at
        )   