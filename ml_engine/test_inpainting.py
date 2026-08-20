import cv2
import numpy as np

from workers.inpainting.inpainting_worker import (
    InpaintingWorker,
)


image = cv2.imread(
    "ml_engine/test_data/sample.jpg"
)

if image is None:
    raise ValueError(
        "Could not load sample image"
    )


# Create a demo mask
mask = np.zeros(
    image.shape[:2],
    dtype=np.uint8,
)

height, width = mask.shape

# Small rectangular region to reconstruct
cv2.rectangle(
    mask,
    (width // 3, height // 3),
    (width // 2, height // 2),
    255,
    -1,
)


worker = InpaintingWorker(
    radius=3.0
)

result = worker.run(
    image,
    {
        "sensor": "demo",
        "sun_elevation": 45,
        "mask": mask,
    },
)

output = result["image"]

cv2.imwrite(
    "ml_engine/test_data/inpainted_output.jpg",
    output,
)

print("Inpainting successful!")
print("Input size:", image.shape[:2])
print("Output size:", output.shape[:2])
print("Score:", result["score"])
print("Metadata:", result["metadata"])