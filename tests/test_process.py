from pathlib import Path

import pandas as pd

from imageassessmentservice.process import (
    build_target_path,
    ImageSorter,
    sort_to_folders,
)


def test_build_target_path(tmp_path: Path) -> None:
    source_path = tmp_path / "source"
    target_path = tmp_path / "target"

    file_path = source_path / "subdir" / "file.txt"

    target_file_path = build_target_path(file_path, source_path, target_path)

    assert target_file_path == target_path / "subdir" / "file.txt"


def test_image_sorter(tmp_path: Path) -> None:
    source_path = tmp_path / "source"
    target_path = tmp_path / "target"

    image_path = source_path / "subdir" / "image.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.touch()

    image_sorter = ImageSorter(source_path, target_path)
    image_sorter.sort(image_path, 1)

    assert (target_path / "1" / "subdir" / "image.jpg").exists()


def test_sort_to_folders(tmp_path: Path) -> None:
    source_path = tmp_path / "source"
    target_path = tmp_path / "target"

    image_paths = []

    for i in range(1, 4):
        image_path = source_path / f"sub_{i}" / f"image_{i}.jpg"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.touch()

        image_paths.append(image_path)

    ratings_csv_file = tmp_path / "ratings.csv"
    normalized_ratings = pd.DataFrame(
        {
            "image_path": [str(image_path) for image_path in image_paths],
            "rating_new": [1, 3, -1],
        }
    )
    normalized_ratings.to_csv(ratings_csv_file, index=False)

    sort_to_folders(str(ratings_csv_file), str(source_path), str(target_path))

    assert (target_path / "1" / "sub_1" / "image_1.jpg").exists()
    assert (target_path / "3" / "sub_2" / "image_2.jpg").exists()
    assert (target_path / "-1" / "sub_3" / "image_3.jpg").exists()
