import pandas as pd
import pytest
from typing import List
from pathlib import Path

from imageassessmentservice.client import (
    normalize_ratings,
    map_ratings_to_bins,
    infer_on_images,
)


def test_normalize_ratings() -> None:
    ratings = pd.DataFrame(
        {
            "image_path": ["path1", "path2", "path3"],
            "aesthetic": [1, 2, 3],
            "technical": [3, 4, 5],
        }
    )

    normalized_ratings = normalize_ratings(ratings, ["aesthetic", "technical"])

    assert pytest.approx(normalized_ratings["aesthetic_normalized"].mean()) == 0
    assert pytest.approx(normalized_ratings["aesthetic_normalized"].std()) == 1

    assert pytest.approx(normalized_ratings["technical_normalized"].mean()) == 0
    assert pytest.approx(normalized_ratings["technical_normalized"].std()) == 1

    assert pytest.approx(normalized_ratings["overall"].mean()) == 0
    assert pytest.approx(normalized_ratings["overall"].std()) == 1


@pytest.mark.parametrize(
    "ratings,num_bins,expected",
    [
        ([0, 1, 2], 2, [1, 1, 2]),
        ([0, 1, 2, 3.1, 4], 3, [1, 1, 2, 3, 3]),
    ],
)
def test_map_ratings_to_bins(
    ratings: List[int], num_bins: int, expected: List[int]
) -> None:
    ratings = pd.Series(ratings)

    mapped_ratings = map_ratings_to_bins(num_bins, ratings)

    assert mapped_ratings.tolist() == expected


def test_infer_on_images_bad_input(tmp_path: Path) -> None:
    input_folder = tmp_path / "input"

    ratings_output_file = tmp_path / "ratings.csv"

    # Check case where input folder does not exist
    with pytest.raises(FileNotFoundError):
        infer_on_images(str(input_folder), str(ratings_output_file))

    input_folder.mkdir()
    ratings_output_file.touch()

    # Check case where output file exists already
    with pytest.raises(FileExistsError):
        infer_on_images(str(input_folder), str(ratings_output_file))

    # Check case where output file has wrong suffix
    ratings_output_file_bad = tmp_path / "ratings.txt"

    with pytest.raises(ValueError):
        infer_on_images(str(input_folder), str(ratings_output_file_bad))


def test_infer_on_images(tmp_path: Path, mocker) -> None:
    input_folder = tmp_path / "input"
    input_folder.mkdir()

    # Generate several input files to apply infer_on_images:
    input_file_1 = input_folder / "image1.jpg"
    input_file_1.touch()

    input_file_2 = input_folder / "sub_folder" / "image2.JPEG"
    input_file_2.parent.mkdir(parents=True)
    input_file_2.touch()

    input_file_3 = input_folder / "other_file.txt"
    input_file_3.touch()

    ratings_output_file = tmp_path / "ratings.csv"

    # Mock the rate_images function to return a fixed result
    mocker.patch(
        "imageassessmentservice.client.rate_images",
        return_value=(
            pd.DataFrame(
                {
                    "image_path": [input_file_1, input_file_2],
                    "aesthetic": [1, 2],
                    "technical": [2, 4],
                }
            ),
            [input_file_3],
        ),
    )

    infer_on_images(
        input_folder=str(input_folder),
        ratings_output_file=str(ratings_output_file),
        num_bins=2,
    )

    ratings_result = pd.read_csv(ratings_output_file)
    ratings_result.drop(
        columns=["Unnamed: 0"], inplace=True
    )  # Drop index column that is not expected from saved data

    expected_result = pd.DataFrame(
        {
            "image_path": [str(input_file_1), str(input_file_2), str(input_file_3)],
            "rating_new": [1, 2, -1],
        }
    )

    pd.testing.assert_frame_equal(ratings_result, expected_result)
