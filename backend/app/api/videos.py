from fastapi import ( APIRouter, HTTPException, Depends, UploadFile, File ,Form , BackgroundTasks)

from pathlib import Path
import filetype
import uuid


import hashlib
from sqlalchemy.exc import IntegrityError

import logging

from app.services.video_processor import QUALITIES, generate_video_version
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)



from app.schemas.video import VideoResponse , VideoUpdate

from app.models.video import Video

from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal

from app.services.video_processor import generate_video_version

router = APIRouter(
    prefix="/api/videos"
)

def get_video_or_404(db: Session, video_id: int) -> Video:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video



def get_owned_video_or_404(db: Session, video_id: int, user: User) -> Video:
    video = db.get(Video, video_id)
    if video is None or video.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/", response_model=list[VideoResponse])
def get_videos(db: Session = Depends(get_db)):
    

    videos = db.query(Video).all()

    return videos


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int,db: Session = Depends(get_db)):
    

    return get_video_or_404(db, video_id)



 

def delete_video_files(file_name: str) -> None:
    original = UPLOAD_DIR / file_name
    paths = [original] + [
        original.with_name(f"{original.stem}_{q}.mp4") for q in QUALITIES
    ]

    for path in paths:
        path.unlink(missing_ok=True) 

        



@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = get_owned_video_or_404(db, video_id, current_user)

    if video.status == "processing":
        raise HTTPException(status_code=409, detail="Video is still processing")

    file_name = video.file_name
    db.delete(video)
    db.commit()

    delete_video_files(file_name)

    return {"message": "Video deleted successfully"}



@router.patch("/{video_id}", response_model=VideoResponse)
def update_video_partial(
    video_id: int,
    video_data: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = get_owned_video_or_404(db, video_id, current_user)

    for field, value in video_data.model_dump(exclude_unset=True).items():
        setattr(video, field, value)

    db.commit()
    db.refresh(video)

    return video




UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}

MAX_FILE_SIZE = 300 * 1024 * 1024  # 300 MB


def process_video_versions(video_id: int, original_path: Path):
    db = SessionLocal()
    created: dict[str, Path] = {}

    try:
        for quality in QUALITIES:
            output_path = original_path.with_name(
                f"{original_path.stem}_{quality}.mp4"
            )
            created[quality] = output_path

            generate_video_version(
                input_path=original_path,
                output_path=output_path,
                quality=quality,
            )

        video = db.get(Video, video_id)
        if video:
            video.low_file_path = created["low"].name
            video.medium_file_path = created["medium"].name
            video.high_file_path = created["high"].name
            video.status = "completed"
            db.commit()

    except Exception:
        db.rollback()
        logger.exception("Video processing failed for ID %s", video_id)

        for path in created.values():
            path.unlink(missing_ok=True)

        video = db.get(Video, video_id)
        if video:
            video.status = "failed"
            db.commit()

    finally:
        db.close()

@router.post("/upload", response_model=VideoResponse)
def upload_video(
    background_tasks: BackgroundTasks,
    title: str = Form(..., min_length=1, max_length=100),
    description: str | None  = Form(None, max_length=1000),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    title = title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only MP4, WebM, and MOV video files are allowed.",
        )

    kind = filetype.guess(file.file)

    if kind is None:
        raise HTTPException(
            status_code=400,
            detail="Could not determine the file type.",
        )

    if kind.mime not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid video file content.",
        )

    file.file.seek(0)

    stored_name = f"{uuid.uuid4()}.{kind.extension}"
    original_path = UPLOAD_DIR / stored_name


    file_size = 0
    hasher = hashlib.sha256()

    
    
    try:
        with original_path.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail="File size must not exceed 300 MB.",
                    )

                hasher.update(chunk) 
                buffer.write(chunk)

        content_hash = hasher.hexdigest()          

        new_video = Video(
            title=title,
            description=description,
            file_name=original_path.name,
            file_size=file_size,
            content_type=kind.mime,
            content_hash=content_hash,
            owner_id=current_user.id,
            status="processing",
        )

        db.add(new_video)
        db.commit()
        db.refresh(new_video)

    except IntegrityError:

        db.rollback()
        original_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail="This video has already been uploaded.",
        )
    
    except Exception:
        db.rollback()

        if original_path.exists():
            original_path.unlink()

        raise

    background_tasks.add_task(
        process_video_versions,
        new_video.id,
        original_path,
    )

    return new_video
