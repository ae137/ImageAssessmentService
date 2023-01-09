import shutil
from pathlib import Path

import fire
import grpc
import pandas as pd
import tensorflow as tf
from tqdm import tqdm

from imageassessment_pb2 import ImageAssessmentRequest
from imageassessment_pb2_grpc import ImageAssessmentStub

physical_devices = tf.config.list_physical_devices("GPU")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)


def build_target_path(
    file_path: Path, relative_source: Path, relative_target: Path
) -> Path:
    rel_file_path = file_path.relative_to(relative_source)
    return relative_target / rel_file_path


class ImageSorter:
    def __init__(
        self, source_path: Path, target_path: Path, threshold: float, margin: float
    ):
        self.source_path = source_path
        self.target_path = target_path
        self.good_images_path = self.target_path / "good"
        self.bad_images_path = self.target_path / "bad"
        self.unclear_images_path = self.target_path / "unclear"

        self.threshold = threshold
        self.margin = margin

    def sort(self, image_path: Path, rating: float):
        if rating > (self.threshold + self.margin):
            print("Good image:", image_path)
            target_path = build_target_path(
                image_path, self.source_path, self.good_images_path
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, target_path)

        elif rating < (self.threshold - self.margin):
            print("Bad image:", image_path)
            target_path = build_target_path(
                image_path, self.source_path, self.bad_images_path
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, target_path)

        else:
            print("Unclear image:", image_path)
            target_path = build_target_path(
                image_path, self.source_path, self.unclear_images_path
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, target_path)


def infer_on_images(
    source_folder: str, target_folder: str, address: str = "localhost"
) -> None:

    options = [
        (
            "grpc.max_send_message_length",
            25 * 1024**2,
        ),  # Maximum message size of 25 MB
    ]
    channel = grpc.insecure_channel(f"{address}:50051", options=options)
    client = ImageAssessmentStub(channel)

    source_folder_path = Path(source_folder)
    target_folder_path = Path(target_folder)

    file_paths = list(source_folder_path.rglob("*"))

    image_paths = [x for x in file_paths if x.suffix in {".jpg", ".JPG"}]
    other_paths = [x for x in file_paths if x.suffix not in {".jpg", ".JPG"}]

    ratings = []

    print("Obtaining ratings")

    for image_path in tqdm(image_paths):
        image_path_str = str(image_path)
        image_bytes = tf.io.read_file(image_path_str)

        request = ImageAssessmentRequest(
            path=image_path_str, image_bytes=image_bytes.numpy()
        )

        response = client.Assess(request)

        ratings.append(
            {
                "image_path": response.path,
                "aesthetic": response.assessment_aesthetic,
                "technical": response.assessment_technical,
            }
        )

    all_ratings = pd.DataFrame(ratings)

    rating_names = ["aesthetic", "technical"]
    for rating_name in rating_names:
        all_ratings[f"{rating_name}_normalized"] = (
            all_ratings[rating_name] - all_ratings[rating_name].mean()
        ) / all_ratings[rating_name].std()

    all_ratings["overall"] = all_ratings[
        [f"{rating_name}_normalized" for rating_name in rating_names]
    ].mean(axis=1)

    # For now, determine image quality relative to median quality image
    threshold = all_ratings["overall"].quantile(0.5)
    margin = all_ratings["overall"].quantile(2.0 / 3) - threshold

    # Sort images based on relative ratings
    print("Sorting files")
    image_sorter = ImageSorter(
        source_folder_path, target_folder_path, threshold, margin
    )

    for index, row in tqdm(all_ratings.iterrows()):
        overall_rating = row["overall"]
        image_sorter.sort(Path(row["image_path"]), overall_rating)

    # Just copy other files
    print("Copying other files (for completeness)")
    other_files_target_path = target_folder_path / "other"
    for file_path in other_paths:
        if Path(file_path).is_file():
            print("Copying file:", file_path)
            target_path = build_target_path(
                file_path, source_folder_path, other_files_target_path
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)


if __name__ == "__main__":
    fire.Fire(infer_on_images)
