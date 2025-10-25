from sqlalchemy import Column, BigInteger, String

from settings import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return "<User('id={}, name={}', password_hash={}, email={})>".format(
            self.id,
            self.name,
            self.password_hash,
            self.email
        )   