from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.cred_loader import cred_loader

schema = cred_loader.db_creds['schema_name']

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    country = Column(String(50), nullable=True)
    profile_image = Column(String(255), nullable=True)
    is_verified = Column(Integer, default=0)
    is_active = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    sent_chats = relationship(
        "Chats",
        back_populates="sender",
        foreign_keys="Chats.sender_id"
    )
    received_chats = relationship(
        "Chats",
        back_populates="recipient",
        foreign_keys="Chats.recipient_id"
    )

class UserVerification(Base):
    __tablename__ = 'user_verification'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"))
    token = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

class Chats(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_id = Column(ForeignKey("users.id"))
    recipient_id = Column(ForeignKey("users.id"))
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_read = Column(Integer, default=0)

    sender = relationship("Users", back_populates="sent_chats", foreign_keys=[sender_id])
    recipient = relationship("Users", back_populates="received_chats", foreign_keys=[recipient_id])
