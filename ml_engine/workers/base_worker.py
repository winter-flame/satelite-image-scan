from abc import ABC, abstractmethod
from typing import Any


class BaseWorker(ABC):

    @abstractmethod
    def run(
        self,
        image: Any,
        metadata: dict,
    ) -> dict:
        """
        Run the worker.

        Returns:
            {
                "image": enhanced_image,
                "score": {...},
                "metadata": {...}
            }
        """
        pass