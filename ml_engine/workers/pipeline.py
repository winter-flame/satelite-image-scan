from workers.dehazing.dehazing_worker import DehazingWorker
from workers.inpainting.inpainting_worker import InpaintingWorker
from workers.superres_fusion.superres_worker import (
    SuperResolutionWorker,
)


class EnhancementPipeline:

    def __init__(self):

        self.dehazing = DehazingWorker(
            strength=0.7
        )

        self.inpainting = InpaintingWorker(
            radius=3.0
        )

        self.super_resolution = SuperResolutionWorker(
            scale=2
        )

    def run(self, image, metadata):

        # Step 1: Dehazing
        dehaze_result = self.dehazing.run(
            image,
            metadata,
        )

        current_image = dehaze_result["image"]

        # Step 2: Inpainting
        inpaint_result = self.inpainting.run(
            current_image,
            metadata,
        )

        current_image = inpaint_result["image"]

        # Step 3: Super-resolution
        superres_result = self.super_resolution.run(
            current_image,
            metadata,
        )

        current_image = superres_result["image"]

        return {
            "image": current_image,
            "score": {
                "dehazing": dehaze_result["score"],
                "inpainting": inpaint_result["score"],
                "super_resolution": superres_result["score"],
            },
            "metadata": {
                **metadata,
                "pipeline": "dehaze_inpaint_superres",
            },
        }