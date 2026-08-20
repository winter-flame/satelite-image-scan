from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_benchmarks():
    return {"psnr": 34.2, "ssim": 0.92}
