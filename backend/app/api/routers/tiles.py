from fastapi import APIRouter

router = APIRouter()

@router.get("/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int):
    return {"tile": f"{z}/{x}/{y}"}
