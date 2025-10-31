# user auth
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
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
    """Create a new user.

    Args:
        user (user_schema.UserCreate): A Pydantic model containing the user's name, email, password and country.
        background_tasks (BackgroundTasks): A FastAPI BackgroundTasks object for running tasks in the background.
        db (Depends[app.database.get_db]): A database session.

    Returns:
        JSONResponse: A JSON response containing the success status and message.
    Raises:
        HTTPException: If the user with the given email already exists.
    """
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
    """
    Verify a user's email using a verification token sent to their email address.
    Args:
        email (str): The user's email address.
        token (str): The verification token sent to the user's email address.
    Returns:
        HTMLResponse: A HTML response object containing a success or failure message.
    """
    try:

        db_user_email = select(models.Users).where(models.Users.email == email)
        result = await db.execute(db_user_email)
        user = result.scalars().first()
        
        if not user:
            return HTMLResponse(
            """
            <html><body style="font-family:sans-serif;text-align:center;margin-top:80px;">
                <h1 style="color:red;">❌ User not found link</h1>
            </body></html>
            """,
            status_code=404
        )
        
        if user.is_verified:
            return HTMLResponse(
            """
            <html><body style="font-family:sans-serif;text-align:center;margin-top:80px;">
                <h1 style="color:red;"> User already verified !</h1>
            </body></html>
            """,
            status_code=400
        )
        
        user_id = user.id

        chk_verification = select(models.UserVerification).where(
            models.UserVerification.user_id == user_id,
            models.UserVerification.token == token
        )

        result = await db.execute(chk_verification)
        verification_record = result.scalars().first()
        
        if not verification_record:
            return HTMLResponse(
            """
            <html><body style="font-family:sans-serif;text-align:center;margin-top:80px;">
                <h1 style="color:red;">❌ Invalid or expired verification link</h1>
            </body></html>
            """,
            status_code=400
        )
        
        upd_user = select(models.Users).where(models.Users.id == user_id)
        result = await db.execute(upd_user)
        user_record = result.scalars().first()
        
        if not user_record:
            return HTMLResponse(
            """
            <html><body style="font-family:sans-serif;text-align:center;margin-top:80px;">
                <h1 style="color:red;">❌ User not found</h1>
            </body></html>
            """,
            status_code=404
        )
        
        user_record.is_verified = 1
        user_record.is_active = 1

        await db.commit()
        
        return HTMLResponse("""
            <html>
            <head><title>Email Verified</title></head>
            <body style="font-family:Arial, sans-serif; text-align:center; margin-top:80px; background-color:#f9f9f9;">
                <div style="display:inline-block; padding:40px; border-radius:12px; background:white; box-shadow:0 0 12px rgba(0,0,0,0.1);">
                    <div style="font-size:70px; color:green;">✅</div>
                    <h1 style="color:#222;">Email Verified Successfully</h1>
                    <p style="color:#555;">Your account is now active. You can safely close this page or log in to continue.</p>
                </div>
            </body>
            </html>
        """)
    
    except Exception as e:
        print_exc()
        await db.rollback()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})

@router.post("/login")
async def login_user(
    user: user_schema.UserLogin,
    db=Depends(app.database.get_db)
):
    """
    Login a user and generate a JWT token if the credentials are valid.

    Args:
        user (user_schema.UserLogin): A Pydantic model containing the user's email and password.
        db (Depends[app.database.get_db]): A database session.

    Returns:
        JSONResponse: A JSON response containing the success status, message and the JWT token.
    """
    try:
        
        db_user_email = select(models.Users).where(models.Users.email == user.email)
        
        result = await db.execute(db_user_email)
        user_record = result.scalars().first()
        
        if not user_record:
            return JSONResponse(status_code=400, content={"success": 0, "message": "Invalid email or password"})
        
        if not utils.verify_password(user.password, user_record.hashed_password):
            return JSONResponse(status_code=400, content={"success": 0, "message": "Invalid email or password"})
        
        if not user_record.is_verified:
            return JSONResponse(status_code=400, content={"success": 0, "message": "Email is not verified"})
        
        if not user_record.is_active:
            return JSONResponse(status_code=400, content={"success": 0, "message": "User account is not active"})
        
        encoded_jwt = utils.get_jwt_token({"user_id": user_record.id})

        response_data = {

            "token" : encoded_jwt,
            "user_id" : user_record.id,
            "email" : user_record.email,
            "name" : user_record.name,
            "country" : user_record.country
        }
        
        return JSONResponse(status_code=200, content={"success": 1, "message": "Login successful", "data": response_data})
    
    except Exception as e:

        print_exc()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})

@router.get("/me")
async def get_current_user(
    token = Depends(utils.decode_jwt_token),
    db=Depends(app.database.get_db)
):  
    """
    Get the current user details.

    Args:
        token (Depends[utils.decode_jwt_token]): The JWT token of the user.
        db (Depends[app.database.get_db]): The database session.

    Returns:
        JSONResponse: A JSON response object containing the user details.
    """
    try:
        user_id = token['user_id']
        db_user = select(models.Users).where(models.Users.id == user_id)
        result = await db.execute(db_user)
        user_record = result.scalars().first()
        
        if not user_record:
            return JSONResponse(status_code=404, content={"success": 0, "message": "User not found"})
        
        user_data = {
            "email": user_record.email,
            "name": user_record.name,
            "country": user_record.country,
            "profile_image": user_record.profile_image,
            "is_verified": bool(user_record.is_verified),
        }
        
        return JSONResponse(status_code=200, content={"success": 1, "message": "User fetched successfully", "data": user_data})
    
    except Exception as e:
        print_exc()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})

@router.put("/profile")
async def update_profile(
    user: user_schema.UserUpdate,
    token = Depends(utils.decode_jwt_token),
    db=Depends(app.database.get_db)
):
    """Update user profile information.

    Args:
        user (user_schema.UserUpdate): A Pydantic model containing the user's name, country and profile image.
        token (str): A JWT token containing the user's ID.
        db (Depends[app.database.get_db]): A database session.

    Returns:
        JSONResponse: A JSON response object containing a success flag, a message and the updated user data.
    """
    try:
        user_id = token['user_id']
        db_user = select(models.Users).where(models.Users.id == user_id)
        result = await db.execute(db_user)
        user_record = result.scalars().first()
        
        if not user_record:
            return JSONResponse(status_code=404, content={"success": 0, "message": "User not found"})
        
        if user.name:
            user_record.name = user.name
        
        if user.country:
            user_record.country = user.country

        if user.profile_image:
            user_record.profile_image = user.profile_image
        
        await db.commit()
        
        return JSONResponse(status_code=200, content={"success": 1, "message": "Profile updated successfully"})
    
    except Exception as e:
        print_exc()
        await db.rollback()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})
    
router.put("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    token = Depends(utils.decode_jwt_token),
    db=Depends(app.database.get_db)
):
    """Change the password of the user.
    
    Args:
        old_password (str): The current password of the user.
        new_password (str): The new password to be set.
        token (Depends[utils.decode_jwt_token]): The JWT token of the user.
        db (Depends[app.database.get_db]): The database session.
    
    Returns:
        JSONResponse: A JSON response containing the success status and message.
    """
    try:
        user_id = token['user_id']
        db_user = select(models.Users).where(models.Users.id == user_id)
        result = await db.execute(db_user)
        user_record = result.scalars().first()
        
        if not user_record:
            return JSONResponse(status_code=404, content={"success": 0, "message": "User not found"})
        
        if not utils.verify_password(old_password, user_record.hashed_password):
            return JSONResponse(status_code=400, content={"success": 0, "message": "Old password is incorrect"})
        
        user_record.hashed_password = utils.get_hased_password(new_password)
        
        await db.commit()
        
        return JSONResponse(status_code=200, content={"success": 1, "message": "Password changed successfully"})
    
    except Exception as e:
        print_exc()
        await db.rollback()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})