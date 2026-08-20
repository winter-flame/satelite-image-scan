from workers.base_worker import BaseWorker


class ConfidenceWorker(BaseWorker):

    def run(self, image, metadata):

        return {
            "image": image,
            "score": {
                "quality": 1.0,
                "confidence": 1.0,
            },
            "metadata": metadata,
        }
