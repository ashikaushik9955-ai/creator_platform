from fastapi import APIRouter

router = APIRouter(
    prefix="/api"
)


@router.get("/hello")
def say_hello():
    return {"message": "Hello from API Router!"}