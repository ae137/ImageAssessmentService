import numpy as np
import tensorflow as tf

from imageassessmentservice.server import ImageAssessmentService
from imageassessmentservice.imageassessment_pb2 import ImageAssessmentRequest


def test_assess() -> None:
    service = ImageAssessmentService()

    image = tf.io.encode_jpeg(np.zeros((128, 256, 3), dtype=np.uint8))

    request = ImageAssessmentRequest(
        path="path/to/image.jpg", image_bytes=image.numpy()
    )

    response = service.Assess(request, None)

    assert response.path == "path/to/image.jpg"
    assert response.assessment_aesthetic > 2.5
    assert response.assessment_technical > 50.0
