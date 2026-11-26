from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from fastapi.staticfiles import StaticFiles

from app.api.videos import UPLOAD_DIR
from app.api.videos import router as video_router
from app.api.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)
app.include_router(auth_router)


app.mount("/media", StaticFiles(directory=UPLOAD_DIR), name="media")

@app.get("/")
def home():
    return {"message": "CreatorFlow backend is running!"}