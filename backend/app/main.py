from fastapi import FastAPI

from app.api.routes import router
from app.api.videos import router as video_router


app = FastAPI()


app.include_router(router)
app.include_router(video_router)

@app.get("/")
def home():
    return {"message": "CreatorFlow backend is running!"}



