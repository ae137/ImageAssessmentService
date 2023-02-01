import shutil
from pathlib import Path
from typing import Final, List, Tuple

import fire
import grpc
import numpy as np
import pandas as pd
import tensorflow as tf
from tqdm import tqdm

from imageassessment_pb2 import ImageAssessmentRequest
from imageassessment_pb2_grpc import ImageAssessmentStub

physical_devices = tf.config.list_physical_devices("GPU")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

MAX_GRPC_MESSAGE_SIZE_MB: Final[int] = 25


def build_target_path(
    file_path: Path, relative_source: Path, relative_target: Path
) -> Path:
    rel_file_path = file_path.relative_to(relative_source)
    return relative_target / rel_file_path


class ImageSorter:
    def __init__(
        self, source_path: Path, target_path: Path, intervals: pd.IntervalIndex
    ):
        self.source_path = source_path
        self.target_path = target_path

        self.paths = [self.target_path / str(i) for i in range(len(intervals))]
        self.intervals = intervals

    def sort(self, image_path: Path, rating: float):
        target_bucket = self.intervals.get_loc(rating)

        print(f"Image of category {target_bucket}.")
        target_path = build_target_path(
            image_path, self.source_path, self.paths[target_bucket]
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, target_path)


def rate_images(
    image_paths: List[Path], address: str
) -> Tuple[pd.DataFrame, List[Path]]:
    options = [
        (
            "grpc.max_send_message_length",
            MAX_GRPC_MESSAGE_SIZE_MB * 1024**2,
        ),  # Maximum message size in bytes
    ]
    channel = grpc.insecure_channel(f"{address}:50051", options=options)
    client = ImageAssessmentStub(channel)

    ratings = []
    images_with_issues = []

    print("Obtaining ratings")

    for image_path in tqdm(image_paths):
        image_path_str = str(image_path)
        image_bytes = tf.io.read_file(image_path_str)

        request = ImageAssessmentRequest(
            path=image_path_str, image_bytes=image_bytes.numpy()
        )

        try:
            response = client.Assess(request)

            ratings.append(
                {
                    "image_path": response.path,
                    "aesthetic": response.assessment_aesthetic,
                    "technical": response.assessment_technical,
                }
            )

        except:
            print(f"Cannot rate image {image_path}.")
            images_with_issues.append(image_path)

    return pd.DataFrame(ratings), images_with_issues


def normalize_ratings(ratings: pd.DataFrame, rating_names: List[str]) -> pd.DataFrame:
    for rating_name in rating_names:
        ratings[f"{rating_name}_normalized"] = (
            ratings[rating_name] - ratings[rating_name].mean()
        ) / ratings[rating_name].std()

    ratings["overall"] = ratings[
        [f"{rating_name}_normalized" for rating_name in rating_names]
    ].mean(axis=1)

    return ratings


def infer_on_images(
    source_folder: str,
    target_folder: str,
    address: str = "localhost",
    num_buckets: int = 5,
) -> None:
    """
    Run image assessment and sort images according to result.

    Parameters
    ----------
    source_folder
        Folder containing the images to be assessed
    target_folder
        Folder to which the assessed images are copied and sorted
    address
        Host where the image assessment service is running
    num_buckets
        Number of buckets in which to sort the images

    Notes
    -----
    Images are assessed aesthetically and technically using two variants of the MUSIQ algorithm (see arxiv:2108.05997).
    The target folder contains several folders which are named according to the rating (for example "1" for images with
    one star, "2" for images with two stars and so on), and in these folders the relative paths of images from the
    source folder are replicated.
    """

    source_folder_path = Path(source_folder)
    target_folder_path = Path(target_folder)

    file_paths = list(source_folder_path.rglob("*"))

    image_file_endings = {".jpg", ".jpeg"}
    image_paths = [x for x in file_paths if x.suffix.lower() in image_file_endings]
    other_paths = [x for x in file_paths if x.suffix.lower() not in image_file_endings]

    raw_ratings, images_with_issues = rate_images(image_paths, address)

    rating_names = ["aesthetic", "technical"]
    normalized_ratings = normalize_ratings(raw_ratings, rating_names)

    # Determine intervals that are used to rate the images
    quantiles = np.linspace(0.0, 1.0, num_buckets + 1, endpoint=True)
    interval_bounds = np.array(
        [normalized_ratings["overall"].quantile(value) for value in quantiles]
    )
    intervals = pd.IntervalIndex.from_arrays(
        interval_bounds[:-1], interval_bounds[1:], closed="both"
    )

    # Sort images based on relative ratings
    print("Sorting files")
    image_sorter = ImageSorter(source_folder_path, target_folder_path, intervals)

    for index, row in tqdm(normalized_ratings.iterrows()):
        overall_rating = row["overall"]
        image_sorter.sort(Path(row["image_path"]), overall_rating)

    # Just copy other files
    print("Copying other files (for completeness)")
    other_files_target_path = target_folder_path / "other"
    for file_path in [*other_paths, *images_with_issues]:
        if Path(file_path).is_file():
            print("Copying file:", file_path)
            target_path = build_target_path(
                file_path, source_folder_path, other_files_target_path
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)


if __name__ == "__main__":
    fire.Fire(infer_on_images)
