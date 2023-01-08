import fire
import grpc
from glob import glob
from pathlib import Path

import tensorflow as tf

from imageassessment_pb2 import ImageAssessmentRequest
from imageassessment_pb2_grpc import ImageAssessmentStub

physical_devices = tf.config.list_physical_devices("GPU")
tf.config.experimental.set_memory_growth(physical_devices[0], True)


def infer_on_images(images_folder: str, address: str = "localhost") -> None:
    channel = grpc.insecure_channel(f"address:50051")
    client = ImageAssessmentStub(channel)

    images_folder_path = Path(images_folder)

    file_paths = glob(str(images_folder_path) + "/**", recursive=True)
    image_paths = [x for x in file_paths if Path(x).suffix in {".jpg", ".JPG"}]
    other_paths = [x for x in file_paths if Path(x).suffix not in {".jpg", ".JPG"}]

    for image_path in image_paths:
        image_bytes = tf.io.read_file(image_path)

        request = ImageAssessmentRequest(
            path=image_path, image_bytes=image_bytes.numpy()
        )

        response = client.Assess(request)

        print(response)


if __name__ == "__main__":
    fire.Fire(infer_on_images)
