import cv2

from workers.dehazing.dehazing_worker import (
    DehazingWorker,
)


image = cv2.imread(
    "ml_engine/test_data/sample.jpg"
)

if image is None:
    raise ValueError(
        "Could not load sample image"
    )


worker = DehazingWorker(
    strength=0.7
)

result = worker.run(
    image,
    {
        "sensor": "demo",
        "sun_elevation": 45,
    },
)

output = result["image"]

cv2.imwrite(
    "ml_engine/test_data/dehazed_output.jpg",
    output,
)

print("Dehazing successful!")
print("Input size:", image.shape[:2])
print("Output size:", output.shape[:2])
print("Score:", result["score"])
print("Metadata:", result["metadata"])