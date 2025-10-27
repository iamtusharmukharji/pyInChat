from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import app.database
import app.models
import app.utils as utils

router = APIRouter(
    prefix="/ws",
    tags=["Chats"]
    )

@router.websocket("/chat/{recipient_id}")
async def chat_endpoint(
    websocket: WebSocket,
    recipient_id: int,
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
    await websocket.accept()
    try:
        token = utils.decode_jwt_chat_token(token)
        user_id = token['user_id']
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message from user {user_id} to user {recipient_id}: {data}")
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from chat with user {recipient_id}")
