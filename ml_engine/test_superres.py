import cv2

from workers.superres_fusion.superres_worker import (
    SuperResolutionWorker,
)


image = cv2.imread(
    "ml_engine/test_data/sample.jpg"
)

if image is None:
    raise ValueError("Could not load sample image")


worker = SuperResolutionWorker(scale=2)

result = worker.run(
    image,
    {
        "sensor": "demo",
        "sun_elevation": 45,
    },
)

output = result["image"]

cv2.imwrite(
    "ml_engine/test_data/superres_output.jpg",
    output,
)

print("Super-resolution successful!")
print("Input size:", image.shape[:2])
print("Output size:", output.shape[:2])
print("Score:", result["score"])
print("Metadata:", result["metadata"])