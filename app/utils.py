

import smtplib
from app.cred_loader import cred_loader
import jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

auth_header = HTTPBearer()



def get_jwt_token(data: dict) -> str:
    
    SECRET_KEY = cred_loader.db_creds.get('secret_key', 'mysecret')
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def decode_jwt_token(token: HTTPAuthorizationCredentials = Depends(auth_header)):
    SECRET_KEY = cred_loader.db_creds.get('secret_key', 'mysecret')
    ALGORITHM = 'HS256'
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
    
def decode_jwt_chat_token(token: str):
    SECRET_KEY = cred_loader.db_creds.get('secret_key', 'mysecret')
    ALGORITHM = 'HS256'
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def get_hased_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_hased_password(plain_password) == hashed_password

def generate_verification_token() -> str:
    import uuid
    return str(uuid.uuid4())

def send_verification_email(email: str, token: str):
    
    SUBJECT="Veify Your Email - PyInChat"
    TEXT=f"Your account has been created successfully. Please verify your email using the following link:\n\n http://127.0.0.1:8000/user/verify-email?email={email}&token={token}"
 
    s = smtplib.SMTP ('smtp.gmail.com', 587)

    s.starttls()

    sender_email = cred_loader.smtp_creds['email']
    sender_password = cred_loader.smtp_creds['app_password']

    s.login(sender_email, sender_password)

    message = f'Subject: {SUBJECT}\n\n{TEXT}'

    s.sendmail(sender_email, email, message)
    print("mail sent")