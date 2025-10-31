from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.schemas import Chats as chatSchema
from fastapi.responses import JSONResponse
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload
import app.database
import app.models as models
import app.utils as utils
from app.redis_manager import RedisChatManager
from traceback import print_exc
from datetime import datetime
import asyncio, json

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
    )

@router.get('/{recipient_id}/chats')
async def fetch_chat_messages(
        recipient_id: int,
        token: dict = Depends(utils.decode_jwt_token),
        db = Depends(app.database.get_db)
    ):
    """
    Retrieve all chat messages for a specific user.
    Returns:
        List of chat messages.
    """
    try:
        user_id = token['user_id']
        db_chats = select(models.Chats).where(
            or_(
                and_(models.Chats.sender_id == user_id, models.Chats.recipient_id == recipient_id),
                and_(models.Chats.sender_id == recipient_id, models.Chats.recipient_id == user_id)
                )
            ).order_by(models.Chats.created_at.desc())
        
        print(db_chats)
        chats = await db.execute(db_chats)
        chats = chats.scalars().all()
        
        
        return {"success": 1, "message":"Chat messages fetched", "data": chats}
    
    except Exception as e:
        print_exc()
        return JSONResponse(status_code=400, content={"success": 0, "message": str(e)})

@router.websocket("/ws")
async def chat_endpoint(
        websocket: WebSocket,
        token: str,
        db = Depends(app.database.get_db)
    ):
    """
    Establish a WebSocket connection between two users.
    Returns:
        None

    Raises:
        WebSocketDisconnect: If the user disconnects from the chat.
    """
    chatManager = RedisChatManager()
    
    await chatManager.connect_redis()
    await websocket.accept()

    

    # verify token
    try:
        token = utils.decode_jwt_chat_token(token)
    
    except Exception as e:
        resp = {"success": 0, "message": str(e), "type":"system_message"}
        await websocket.send_json(resp)
        await websocket.close()
        return
    
    user_id = token['user_id']
    await chatManager.set_online(user_id)
    
    # verify both users exist and are verified

    db_user = await db.get(models.Users, user_id)
    
    # check if users exist
    if not db_user:
        resp = {"success": 0, "message": "User not found"}
        await websocket.send_json(resp)
        await websocket.close()
        return
    
    # check if user is verified
    if db_user.is_verified == False:
        resp = {"success": 0, "message": "Email not verified"}
        await websocket.send_json(resp)
        await websocket.close()
        return
    
    try:
        msg_listen_bg_task = asyncio.create_task(chatManager.listen_messages(user_id, websocket))
        
        while True:
            
            """
            Expected message format:
            {
                "message":"How are you today?",
                "type":"user_message",
                "to_user_id":17
            }

            """ 
            

            data = await websocket.receive_json()
            try:
                
                # validate incomming message using pydantic schema
                data = chatSchema.ChatMessage(**data)

            except Exception as e:
                await websocket.send_json({"success": 0, "message": "Invalid message format", "type":"system_message"})
                continue
            
            # setattr(data, 'type', "user_message")
            
            chat_topic = f"chat_{data.to_user_id}"
            dict_msg = data.dict()
            dict_msg['from_user_id'] = user_id
            dict_msg["from_username"] = db_user.name


            # Publish the message to the Redis channel
            dict_to_str_msg = json.dumps(dict_msg)
            
            is_sent = await chatManager.publish(chat_topic, dict_to_str_msg)
            
            if not is_sent:
                await websocket.send_json({"success": 0, "message": "Failed to send message", "type":"system_message"})
                continue

            # Store the chat message in the database
            new_chat = models.Chats(
                sender_id=user_id,
                recipient_id=data.to_user_id,
                message=data.message,
                created_at=datetime.now(),
            )

            db.add(new_chat)
            await db.commit()

            await websocket.send_json(
                { "success": 1, "message": "Message sent successfully", "data": { "chat_id": new_chat.id }, "type":"system_message" }
            )
    
    except WebSocketDisconnect:
        # print(f"User {user_id} disconnected from chat")
        await chatManager.set_offline(user_id)
        msg_listen_bg_task.cancel()
        


