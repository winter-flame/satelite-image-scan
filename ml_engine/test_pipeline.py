import cv2

from workers.pipeline import EnhancementPipeline


image = cv2.imread(
    "ml_engine/test_data/sample.jpg"
)

if image is None:
    raise ValueError(
        "Could not load sample image"
    )


metadata = {
    "sensor": "demo",
    "sun_elevation": 45,
}


pipeline = EnhancementPipeline()

result = pipeline.run(
    image,
    metadata,
)


output = result["image"]

cv2.imwrite(
    "ml_engine/test_data/pipeline_output.jpg",
    output,
)


print("FULL PIPELINE SUCCESSFUL!")
print("Input size:", image.shape[:2])
print("Output size:", output.shape[:2])

print("\nScores:")
print(result["score"])

print("\nMetadata:")
print(result["metadata"])