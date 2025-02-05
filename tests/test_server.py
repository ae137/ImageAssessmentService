import numpy as np
import tensorflow as tf

from imageassessmentservice.server import ImageAssessmentService
from imageassessment_pb2 import ImageAssessmentRequest


def test_assess() -> None:
    service = ImageAssessmentService()

    image = tf.io.encode_jpeg(np.zeros((128, 256, 3), dtype=np.uint8))

    request = ImageAssessmentRequest(
        image_path="path/to/image.jpg", image_hash="abcdefg", image_bytes=image.numpy()
    )

    response = service.Assess(request, None)

    assert response.image_path == "path/to/image.jpg"
    assert response.image_hash == "abcdefg"
    assert response.assessment_aesthetic > 2.5
    assert response.assessment_technical > 50.0
