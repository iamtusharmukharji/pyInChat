

import smtplib
from app.cred_loader import cred_loader

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