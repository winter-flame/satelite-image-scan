from workers.base_worker import BaseWorker


class DummyWorker(BaseWorker):

    def run(
        self,
        image,
        metadata: dict,
    ) -> dict:

        return {
            "image": image,
            "score": {
                "quality": 1.0,
                "confidence": 1.0,
            },
            "metadata": metadata,
        }