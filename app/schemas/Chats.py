from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class MessageType(str, Enum):
    STSYEM = "system_message"
    USER = "user_message"

class ChatMessage(BaseModel):
    message: str
    to_user_id: int
    type:  MessageType  # default type is user_message