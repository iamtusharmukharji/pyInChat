# user auth
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi import Depends
from app import models, utils
from app.schemas import Users as user_schema
from sqlalchemy import select
from traceback import print_exc
import app.database

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/signup", status_code=201)
async def create_user(
    user: user_schema.UserCreate,
    background_tasks: BackgroundTasks,
    db=Depends(app.database.get_db)
    
):
    try:
        chk_user = select(models.Users).where(models.Users.email == user.email)
        result = await db.execute(chk_user)
        existing_user = result.scalars().first()
        
        if existing_user:
            return JSONResponse(status_code=400, content={"success": 0, "message": "User with this email already exists"})
        

        new_user = models.Users(
            name=user.name,
            username=user.email.split('@')[0],
            email=user.email,
            hashed_password=utils.get_hased_password(user.password),
            country=user.country
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        verification_token = utils.generate_verification_token()
        new_verification = models.UserVerification()
        new_verification.user_id = new_user.id
        new_verification.token = verification_token

        db.add(new_verification)
        await db.commit()
        await db.refresh(new_verification)
        
        #send verification email logic can be added here
        # utils.send_verification_email(new_user.email, verification_token)
       
        background_tasks.add_task(utils.send_verification_email, new_user.email, verification_token)

        return JSONResponse(status_code=201, content={"success": 1, "message": "User created successfully, verify your email", "user_id": new_user.id})
    
    except Exception as e:
        print_exc()
        await db.rollback()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})


@router.get("/verify-email")
async def verify_email(
    email: str,
    token: str,
    db=Depends(app.database.get_db)
):
    try:

        db_user_email = select(models.Users).where(models.Users.email == email)
        result = await db.execute(db_user_email)
        user = result.scalars().first()
        
        if not user:
            return JSONResponse(status_code=400, content={"success": 0, "message": "User not found"})
        
        if user.is_verified:
            return JSONResponse(status_code=400, content={"success": 0, "message": "User is already verified"})
        
        user_id = user.id

        chk_verification = select(models.UserVerification).where(
            models.UserVerification.user_id == user_id,
            models.UserVerification.token == token
        )

        result = await db.execute(chk_verification)
        verification_record = result.scalars().first()
        
        if not verification_record:
            return JSONResponse(status_code=400, content={"success": 0, "message": "Invalid verification token or user ID"})
        
        upd_user = select(models.Users).where(models.Users.id == user_id)
        result = await db.execute(upd_user)
        user_record = result.scalars().first()
        
        if not user_record:
            return JSONResponse(status_code=400, content={"success": 0, "message": "User not found"})
        
        user_record.is_verified = 1
        await db.commit()
        
        return JSONResponse(status_code=200, content={"success": 1, "message": "Email verified successfully"})
    
    except Exception as e:
        print_exc()
        await db.rollback()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})


