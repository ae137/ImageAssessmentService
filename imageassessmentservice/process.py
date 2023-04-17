import shutil
import sqlite3
from pathlib import Path
from typing import Any

import fire
import pandas as pd
from tqdm import tqdm


def build_rating_update_command(image_id, rating):
    command = f"""UPDATE ImageInformation
    SET rating = {rating}
    WHERE
        imageid = {image_id};"""
    return command


# TODO: Add tests
def update_rating(connection: Any, image_id: str, rating: int) -> None:
    """
    Update rating of image in Digikam database

    Parameters
    ----------
    connection
        SQLite connection to Digikam database
    image_id
        ID of image to update
    rating
        New rating of image
    """
    cursor = connection.cursor()
    command = build_rating_update_command(image_id, rating)

    cursor.execute(command)

    connection.commit()


# TODO: Add tests
def load_digikam_image_data(database_file_path: Path) -> pd.DataFrame:
    """
    Load image data from Digikam database

    Parameters
    ----------
    database_file_path
        Path to Digikam database file (digikam4.db)

    Returns
    -------
    Dataframe with relevant information from Digikam database
    """
    connection = sqlite3.connect(database_file_path)

    album_roots_table = pd.read_sql_query(
        "SELECT id, specificPath FROM AlbumRoots;", connection
    )
    album_roots_table.rename(columns={"id": "album_root_id"}, inplace=True)

    albums_table = pd.read_sql_query(
        "SELECT id, albumRoot, relativePath FROM Albums;", connection
    )
    albums_table.rename(
        columns={"id": "album_id", "albumRoot": "album_root_id"}, inplace=True
    )

    images_table = pd.read_sql_query("SELECT id, album, name FROM Images;", connection)
    images_table.rename(columns={"id": "image_id", "album": "album_id"}, inplace=True)

    image_information_table = pd.read_sql_query(
        "SELECT imageid, rating FROM ImageInformation;", connection
    )
    image_information_table.rename(
        columns={"imageid": "image_id", "rating": "rating_old"}, inplace=True
    )

    data_table = images_table.merge(
        albums_table, left_on="album_id", right_on="album_id"
    )
    data_table = data_table.merge(
        album_roots_table, left_on="album_root_id", right_on="album_root_id"
    )
    data_table = data_table.merge(
        image_information_table, left_on="image_id", right_on="image_id"
    )

    data_table["full_path"] = data_table.apply(
        lambda x: "/home" + x["specificPath"] + x["relativePath"] + "/" + x["name"],
        axis=1,
    )
    # Here we can drop even more columns as only fullPath and rating are required
    data_table.drop(
        columns=["album_id", "name", "album_root_id", "relativePath", "specificPath"],
        inplace=True,
    )

    return data_table


# TODO: Add tests
def store_to_digikam_db(
    database_file: str,
    ratings_file: str,
):
    """Store results of image assessment in SQLite database for Digikam

    Parameters
    ----------
    database_file
        Path to file containing the SQLite database (digikam4.db)
    ratings_file
        Table containing paths to image files and ratings
    """
    database_file_path = Path(database_file)
    ratings_file_path = Path(ratings_file)

    if database_file_path.name != "digikam4.db":
        raise ValueError("Obtained unexpected name for database")

    if not database_file_path.exists():
        raise FileNotFoundError("Cannot find database file")

    if not ratings_file_path.exists():
        raise FileNotFoundError("Cannot find file with ratings.")

    # Load and merge tables
    data_table = load_digikam_image_data(database_file_path)

    # Load ratings
    int_ratings = pd.read_csv(ratings_file_path)
    merged_table = int_ratings.merge(
        data_table, left_on="image_path", right_on="full_path"
    )

    # Update ratings
    for _, row in merged_table.iterrows():
        image_id, image_path, rating_new = row[["image_id", "image_path", "rating_new"]]

        if rating_new < 0:
            continue

        try:
            connection_for_update = sqlite3.connect(database_file_path)

            print("Updating ", image_path)
            update_rating(connection_for_update, image_id, rating_new)
        except Exception as e:
            print(e)
            print("Failed to update rating for ", image_path)


def build_target_path(
    file_path: Path, relative_source: Path, relative_target: Path
) -> Path:
    """
    Build target path for file based on source and target path.

    Parameters
    ----------
    file_path
        Input path
    relative_source
        Path relative to which the file_path is taken
    relative_target
        Path relative to which the target path is built

    Returns
    -------
    Target path
    """
    rel_file_path = file_path.relative_to(relative_source)
    return relative_target / rel_file_path


class ImageSorter:
    def __init__(self, source_path: Path, target_path: Path):
        self.source_path = source_path
        self.target_path = target_path

    def sort(self, image_path: Path, int_rating: int):

        print(f"Image of category {int_rating}.")
        target_path = build_target_path(
            image_path, self.source_path, self.target_path / f"{int_rating}"
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, target_path)


def sort_to_folders(
    ratings_csv_file: str, source_folder: str, target_folder: str
) -> None:
    """
    Sort images based on ratings to folders.

    Parameters
    ----------
    ratings_csv_file
        CSV file containing ratings
    source_folder
        Folder containing images (and relative paths in the target folder are taken with respect to this root folder).
    target_folder
        Target folder where images are sorted to.
    """
    normalized_ratings = pd.read_csv(ratings_csv_file)

    source_folder_path = Path(source_folder)
    target_folder_path = Path(target_folder)

    # Sort images based on relative ratings
    print("Sorting files")
    image_sorter = ImageSorter(source_folder_path, target_folder_path)

    for _, row in tqdm(normalized_ratings.iterrows()):
        image_sorter.sort(Path(row["image_path"]), row["rating_new"])


if __name__ == "__main__":
    fire.Fire({"digikam": store_to_digikam_db, "sort": sort_to_folders})
