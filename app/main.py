# fastapi application entry point
from fastapi import FastAPI
from fastapi import Depends
from fastapi.responses import RedirectResponse
from app.routers import users, chats
from app.database import get_db




async def startup_event():
    # redis_instance = RedisManager()
    # await redis_instance.connect_redis()
    # app.state.redis = redis_instance
    pass

async def shutdown_event():
    # redis = app.state.redis
    # redis.set_value("active_connections", {})
    # await redis.redis.close()
    pass

app = FastAPI(
    title="PyInChat",
    version="0.1.1",
    description="A chat application backend using FastAPI",
    on_startup=[startup_event],
    on_shutdown=[shutdown_event]
)

app.include_router(users.router)
app.include_router(chats.router)




@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get('/db-health')
async def db_health_check(db=Depends(get_db)):
    return {"success": 1, "message": "database is healthy"}


