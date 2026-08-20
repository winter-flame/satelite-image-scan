from dataclasses import dataclass
from typing import Any


@dataclass
class WorkerResult:
    image: Any
    score: dict
    metadata: dict