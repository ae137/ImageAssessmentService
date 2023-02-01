import pandas as pd

from imageassessmentservice.ratings_cache import RatingsCache


def test_create_ratings_cache(tmp_path) -> None:
    cache = RatingsCache(tmp_path / "cache_data.csv")

    assert "image_hash_sha256" in cache.data.columns
    assert len(cache) == 0


def test_update_ratings_cache(tmp_path) -> None:
    cache_storage_path = tmp_path / "cache_data.csv"
    data = pd.DataFrame(
        {
            "image_hash_sha256": ["ab", "cd"],
            "aesthetic": [1.0, 1.5],
            "technical": [3.5, 1.0],
        }
    )
    data_updated = pd.DataFrame(
        {
            "image_hash_sha256": ["ab", "cd", "ef"],
            "aesthetic": [1.0, 2.5, 5.0],
            "technical": [3.5, 0.0, 4.0],
        }
    )

    data.to_csv(cache_storage_path, index=False)

    cache = RatingsCache(cache_storage_path)
    pd.testing.assert_frame_equal(data, cache.data)

    cache.update("cd", {"aesthetic": 2.5, "technical": 0.0})
    cache.update("ef", {"aesthetic": 5.0, "technical": 4.0})

    pd.testing.assert_frame_equal(data_updated, cache.data)


def test_retrieve_ratings(tmp_path) -> None:
    cache_storage_path = tmp_path / "cache_data.csv"
    data = pd.DataFrame(
        {
            "image_hash_sha256": ["ab", "cd"],
            "aesthetic": [1.0, 1.5],
            "technical": [3.5, 1.0],
        }
    )
    data.to_csv(cache_storage_path, index=False)

    cache = RatingsCache(cache_storage_path)

    assert cache.retrieve("xyz") == {}

    assert cache.retrieve("cd") == {"aesthetic": 1.5, "technical": 1.0}
