from sqlalchemy import Column, BigInteger, String

from settings import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)

    def __repr__(self):
        return "<User('id={}, name={}', password={}, email={})>".format(
            self.id,
            self.name,
            self.password,
            self.email
        )   