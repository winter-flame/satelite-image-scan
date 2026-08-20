import cv2
import numpy as np

from workers.base_worker import BaseWorker


class DehazingWorker(BaseWorker):

    def __init__(self, strength: float = 0.7):
        self.strength = strength

    def run(self, image, metadata):

        if image is None:
            raise ValueError("Input image is None")

        # Convert image to float for processing
        image_float = image.astype(np.float32) / 255.0

        # Estimate atmospheric light
        dark_channel = self._dark_channel(
            image_float,
            kernel_size=15,
        )

        atmospheric_light = self._estimate_atmospheric_light(
            image_float,
            dark_channel,
        )

        # Estimate transmission
        transmission = 1.0 - self.strength * dark_channel

        transmission = np.clip(
            transmission,
            0.1,
            1.0,
        )

        # Recover scene radiance
        transmission_3 = transmission[:, :, np.newaxis]

        recovered = (
            image_float - atmospheric_light
        ) / transmission_3 + atmospheric_light

        recovered = np.clip(
            recovered,
            0.0,
            1.0,
        )

        enhanced = (
            recovered * 255
        ).astype(np.uint8)

        return {
            "image": enhanced,
            "score": {
                "dehaze_strength": self.strength,
                "transmission_mean": float(
                    np.mean(transmission)
                ),
            },
            "metadata": {
                **metadata,
                "worker": "dehazing",
                "method": "dark_channel_prior",
            },
        }

    def _dark_channel(
        self,
        image,
        kernel_size=15,
    ):

        minimum = np.min(
            image,
            axis=2,
        )

        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (kernel_size, kernel_size),
        )

        dark = cv2.erode(
            minimum,
            kernel,
        )

        return dark

    def _estimate_atmospheric_light(
        self,
        image,
        dark_channel,
    ):

        height, width = dark_channel.shape

        total_pixels = height * width

        number = max(
            1,
            int(total_pixels * 0.001),
        )

        flat_dark = dark_channel.reshape(-1)

        indices = np.argsort(
            flat_dark
        )[-number:]

        flat_image = image.reshape(
            -1,
            3,
        )

        atmospheric = np.mean(
            flat_image[indices],
            axis=0,
        )

        return atmospheric