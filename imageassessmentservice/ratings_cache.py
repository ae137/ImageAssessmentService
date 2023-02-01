from pathlib import Path

import pandas as pd
from imageassessmentservice.definitions import RATING_NAMES


class RatingsCache:
    def __init__(self, ratings_cache_file: str | Path):
        self.ratings_cache_path = Path(ratings_cache_file)

        if (
            self.ratings_cache_path.exists()
            and self.ratings_cache_path.suffix != ".csv"
        ):
            raise ValueError("Ratings file exists but is not a 'csv' file.")

        self.data = (
            pd.read_csv(self.ratings_cache_path, index_col=False)
            if self.ratings_cache_path.exists()
            else pd.DataFrame(
                {"image_hash_sha256": [], **{name: [] for name in RATING_NAMES}}
            )
        )

    def __len__(self):
        return len(self.data)

    def contains(self, image_hash_sha256: str) -> bool:
        return image_hash_sha256 in self.data["image_hash_sha256"].values

    def retrieve(self, image_hash_sha256: str) -> dict[str, float]:
        if self.contains(image_hash_sha256):
            row = self.data.loc[
                self.data["image_hash_sha256"] == image_hash_sha256
            ].to_dict("records")
            assert len(row) == 1
            return {rating_name: row[0][rating_name] for rating_name in RATING_NAMES}
        else:
            return {}

    def update(self, image_hash_sha256: str, ratings: dict[str, float]) -> None:
        if self.contains(image_hash_sha256):
            for rating_name, rating_value in ratings.items():
                self.data.loc[
                    self.data["image_hash_sha256"] == image_hash_sha256, rating_name
                ] = rating_value
        else:
            new_row = pd.DataFrame(
                [{"image_hash_sha256": image_hash_sha256, **ratings}]
            )
            self.data = pd.concat([self.data, new_row], ignore_index=True)

    def store(self) -> None:
        # TODO: this hould be done via context manager instead
        self.data.to_csv(self.ratings_cache_path, index=False)
