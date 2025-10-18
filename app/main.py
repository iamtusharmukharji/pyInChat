# fastapi application entry point
from fastapi import FastAPI
from fastapi import Depends
from fastapi.responses import RedirectResponse
from app.routers import users
from app.database import get_db

app = FastAPI(
    title="PyInChat",
    version="0.1.1",
    description="A chat application backend using FastAPI"
)

app.include_router(users.router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get('/db-health')
async def db_health_check(db=Depends(get_db)):
    return {"success": 1, "message": "database is healthy"}


