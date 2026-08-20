import cv2

from workers.superres_fusion.superres_worker import (
    SuperResolutionWorker,
)


# Load original high-quality image
original = cv2.imread(
    "ml_engine/test_data/sample.jpg"
)

if original is None:
    raise ValueError("Could not load sample image")


# Create artificial low-resolution input
height, width = original.shape[:2]

low_res = cv2.resize(
    original,
    (width // 2, height // 2),
    interpolation=cv2.INTER_AREA,
)


# Run super-resolution
worker = SuperResolutionWorker(scale=2)

result = worker.run(
    low_res,
    {
        "sensor": "demo",
        "sun_elevation": 45,
    },
    reference=original,
)


print("Super-resolution metrics:")
print(result["score"])