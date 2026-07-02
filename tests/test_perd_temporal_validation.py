import pandas as pd

from perd.temporal_validation import split_by_year


def test_split_by_year_correctly_splits_train_test() -> None:
    df = pd.DataFrame({"sample_id": ["old", "new"], "year": [2020, 2023]})

    train, test = split_by_year(df, train_end_year=2021, test_start_year=2022)

    assert train["sample_id"].tolist() == ["old"]
    assert test["sample_id"].tolist() == ["new"]
