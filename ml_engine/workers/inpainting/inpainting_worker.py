import cv2
import numpy as np

from workers.base_worker import BaseWorker


class InpaintingWorker(BaseWorker):

    def __init__(self, radius: float = 3.0):
        self.radius = radius

    def run(self, image, metadata):

        if image is None:
            raise ValueError("Input image is None")

        # Get mask from metadata
        mask = metadata.get("mask")

        if mask is None:
            # Nothing to inpaint
            return {
                "image": image,
                "score": {
                    "inpainted_pixels": 0,
                    "mask_present": False,
                },
                "metadata": {
                    **metadata,
                    "worker": "inpainting",
                    "method": "none",
                },
            }

        # Convert mask to NumPy array
        mask = np.asarray(mask)

        if mask.shape[:2] != image.shape[:2]:
            raise ValueError(
                "Mask dimensions must match image dimensions"
            )

        # Ensure binary 8-bit mask
        mask = np.where(
            mask > 0,
            255,
            0,
        ).astype(np.uint8)

        # Count pixels that will be reconstructed
        inpainted_pixels = int(
            np.count_nonzero(mask)
        )

        # OpenCV Telea inpainting
        result = cv2.inpaint(
            image,
            mask,
            self.radius,
            cv2.INPAINT_TELEA,
        )

        return {
            "image": result,
            "score": {
                "inpainted_pixels": inpainted_pixels,
                "mask_present": True,
            },
            "metadata": {
                **metadata,
                "worker": "inpainting",
                "method": "opencv_telea",
            },
        }