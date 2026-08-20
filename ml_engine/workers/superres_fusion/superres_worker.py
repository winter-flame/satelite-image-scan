import cv2
import numpy as np

from skimage.metrics import peak_signal_noise_ratio
from skimage.metrics import structural_similarity

from workers.base_worker import BaseWorker


class SuperResolutionWorker(BaseWorker):

    def __init__(self, scale: int = 2):
        self.scale = scale

    def run(self, image, metadata, reference=None):

        if image is None:
            raise ValueError("Input image is None")

        height, width = image.shape[:2]

        # Upscale using bicubic interpolation
        enhanced = cv2.resize(
            image,
            (width * self.scale, height * self.scale),
            interpolation=cv2.INTER_CUBIC,
        )

        # Mild sharpening
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ])

        enhanced = cv2.filter2D(
            enhanced,
            -1,
            kernel,
        )

        # Initialize scores
        scores = {
            "scale": self.scale,
        }

        # Calculate PSNR and SSIM when reference image is provided
        if reference is not None:

            reference_resized = cv2.resize(
                reference,
                (enhanced.shape[1], enhanced.shape[0]),
                interpolation=cv2.INTER_CUBIC,
            )

            enhanced_rgb = cv2.cvtColor(
                enhanced,
                cv2.COLOR_BGR2RGB,
            )

            reference_rgb = cv2.cvtColor(
                reference_resized,
                cv2.COLOR_BGR2RGB,
            )

            scores["psnr"] = peak_signal_noise_ratio(
                reference_rgb,
                enhanced_rgb,
                data_range=255,
            )

            scores["ssim"] = structural_similarity(
                reference_rgb,
                enhanced_rgb,
                channel_axis=2,
                data_range=255,
            )

        return {
            "image": enhanced,
            "score": scores,
            "metadata": {
                **metadata,
                "worker": "super_resolution",
                "method": "bicubic",
            },
        }