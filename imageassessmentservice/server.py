from concurrent import futures

import fire
import grpc

import numpy as np
import tensorflow as tf
import tensorflow_hub as tf_hub

from imageassessment_pb2 import ImageAssessmentResponse
from imageassessment_pb2_grpc import (
    ImageAssessmentServicer,
    add_ImageAssessmentServicer_to_server,
)

physical_devices = tf.config.list_physical_devices("GPU")
tf.config.experimental.set_memory_growth(physical_devices[0], True)


class ImageAssessmentService(ImageAssessmentServicer):
    def __init__(self):
        self.musiq_model_ava = tf_hub.load("https://tfhub.dev/google/musiq/ava/1")
        self.predict_fn_musiq_ava = self.musiq_model_ava.signatures["serving_default"]

        self.musiq_model_paq2piq = tf_hub.load(
            "https://tfhub.dev/google/musiq/paq2piq/1"
        )
        self.predict_fn_musiq_paq2piq = self.musiq_model_paq2piq.signatures[
            "serving_default"
        ]

        print("Ready to assess images")

    def Assess(self, request, context):
        image_bytes_tensor = tf.constant(request.image_bytes)

        output_musiq_ava = self.predict_fn_musiq_ava(image_bytes_tensor)
        rating_ava = output_musiq_ava["output_0"].numpy()

        output_musiq_paq2piq = self.predict_fn_musiq_paq2piq(image_bytes_tensor)
        rating_paq2piq = output_musiq_paq2piq["output_0"].numpy()

        return ImageAssessmentResponse(
            path=request.path,
            assessment_aesthetic=rating_ava,
            assessment_technical=rating_paq2piq,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ImageAssessmentServicer_to_server(ImageAssessmentService(), server)

    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    fire.Fire(serve)
