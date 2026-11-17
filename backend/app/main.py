from fastapi import FastAPI


from app.api.videos import router as video_router
from app.api.auth import router as auth_router

app = FastAPI()



app.include_router(video_router)
app.include_router(auth_router)

@app.get("/")
def home():
    return {"status": "ok", "service": "CreatorFlow backend"}



