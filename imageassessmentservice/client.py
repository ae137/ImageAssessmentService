from pathlib import Path
from typing import Any, List, Tuple

import fire
import grpc
import numpy as np
import pandas as pd
import tensorflow as tf
from tqdm import tqdm

from imageassessmentservice.definitions import MAX_GRPC_MESSAGE_SIZE_MB
from imageassessmentservice.imageassessment_pb2 import ImageAssessmentRequest
from imageassessmentservice.imageassessment_pb2_grpc import ImageAssessmentStub

physical_devices = tf.config.list_physical_devices("GPU")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)


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

        except Exception as e:
            print(f"Cannot rate image {image_path}.")
            images_with_issues.append(image_path)

    return pd.DataFrame(ratings), images_with_issues


def normalize_ratings(ratings: pd.DataFrame, rating_names: List[str]) -> pd.DataFrame:
    """Normalize ratings to have zero mean and unit variance.

    Parameters
    ----------
    ratings
        Dataframe containing ratings data
    rating_names
        Names of the ratings to normalize and combine by averaging

    Returns
    -------
    Dataframe with normalized ratings and an overall rating
    """
    for rating_name in rating_names:
        ratings[f"{rating_name}_normalized"] = (
            ratings[rating_name] - ratings[rating_name].mean()
        ) / ratings[rating_name].std()

    ratings["overall"] = ratings[
        [f"{rating_name}_normalized" for rating_name in rating_names]
    ].mean(axis=1)

    ratings.drop(columns=rating_names, inplace=True)

    return ratings


def map_ratings_to_bins(num_bins: int, ratings: pd.Series) -> pd.Series:
    """Reduce floating point ratings to integer values by mapping them to bins.

    Parameters
    ----------
    num_bins
        Number of bins to sort the ratings into
    ratings
        Rating values

    Returns
    -------
    Series of ratings mapped to bins
    """
    quantiles = np.linspace(0.0, 1.0, num_bins + 1, endpoint=True)
    interval_bounds = np.array([ratings.quantile(value) for value in quantiles])
    intervals = pd.IntervalIndex.from_arrays(
        interval_bounds[:-1], interval_bounds[1:], closed="both"
    )

    def _get_int_rating(
        ratings_float: float,
        intervals_for_ratings: pd.IntervalIndex,
        ratings_int: List[int],
    ) -> Any:
        interval_idx = intervals_for_ratings.get_loc(ratings_float)
        rating = ratings_int[interval_idx]

        return rating if isinstance(rating, int) else rating[0]

    target_ratings = list(range(1, num_bins + 1))
    mapped_ratings = ratings.apply(
        lambda x: _get_int_rating(x, intervals, target_ratings)
    )
    return mapped_ratings


def infer_on_images(
    input_folder: str,
    ratings_output_file: str,
    address: str = "localhost",
    num_bins: int = 5,
) -> None:
    """
    Run image assessment and sort images according to result.

    Parameters
    ----------
    input_folder
        Folder containing the images to be assessed
    ratings_output_file
        File to which the ratings should be stored
    address
        Host where the image assessment service is running
    num_bins
        Number of bins in which to sort the images
    """

    source_folder_path = Path(input_folder)
    ratings_output_file_path = Path(ratings_output_file)

    if not source_folder_path.exists() or source_folder_path.is_file():
        raise FileNotFoundError("Input folder does not exist or is a file.")

    if ratings_output_file_path.exists():
        raise FileExistsError("Output file exists already. It will not be overwritten.")

    if ratings_output_file_path.suffix != ".csv":
        raise ValueError("Expect output file to have suffix 'csv'.")

    file_paths = list(source_folder_path.rglob("*"))

    image_file_endings = {".jpg", ".jpeg"}
    image_paths = [x for x in file_paths if x.suffix.lower() in image_file_endings]
    other_paths = [
        x
        for x in file_paths
        if not (x.suffix.lower() in image_file_endings or x.is_dir())
    ]

    raw_ratings, images_with_issues = rate_images(image_paths, address)

    rating_names = ["aesthetic", "technical"]
    normalized_ratings = normalize_ratings(raw_ratings, rating_names)

    normalized_ratings["rating_new"] = map_ratings_to_bins(
        num_bins, normalized_ratings["overall"]
    )

    rating_data = normalized_ratings[["image_path", "rating_new"]]

    files_without_ratings = pd.DataFrame(
        {"image_path": other_paths, "rating_new": [-1] * len(other_paths)}
    )

    all_data = pd.concat([rating_data, files_without_ratings], ignore_index=True)
    all_data["rating_new"] = all_data["rating_new"].astype(int)

    all_data.to_csv(ratings_output_file_path)


if __name__ == "__main__":
    fire.Fire(infer_on_images)
