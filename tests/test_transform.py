"""Unit test untuk memvalidasi proses transformasi data."""

from __future__ import annotations

import pandas as pd

from utils import transform as transform_module
from utils.transform import (
    clean_colors,
    clean_gender,
    clean_rating,
    clean_size,
    clean_timestamp,
    clean_title,
    convert_price_to_rupiah,
    create_empty_dataframe,
    transform_data,
)


def test_convert_price_to_rupiah_from_usd():
    """Memastikan harga USD berhasil dikonversi ke rupiah."""
    assert convert_price_to_rupiah("$10.00") == 160000.0


def test_clean_rating_returns_float():
    """Memastikan rating dibersihkan menjadi float."""
    assert clean_rating("4.8 / 5") == 4.8


def test_clean_colors_returns_int():
    """Memastikan jumlah warna dibersihkan menjadi integer."""
    assert clean_colors("3 Colors") == 3


def test_helper_functions_handle_invalid_values():
    """Memastikan helper transform mengembalikan None untuk nilai invalid."""
    assert clean_title("Unknown Product") is None
    assert convert_price_to_rupiah("Price Unavailable") is None
    assert clean_rating("Not Rated") is None
    assert clean_colors("Rating: Not Rated") is None
    assert clean_size("8 Colors") is None
    assert clean_gender("Size: S") is None
    assert clean_timestamp(None) is None


def test_transform_data_removes_null_duplicates_and_invalid_rows():
    """Memastikan data null, duplikat, dan invalid dihapus saat transformasi."""
    raw_data = [
        {
            "Title": "T-shirt 2",
            "Price": "$102.15",
            "Rating": "3.9 / 5",
            "Colors": "3 Colors",
            "Size": "M",
            "Gender": "Women",
            "Timestamp": "2025-02-10T13:54:32.640365",
        },
        {
            "Title": "T-shirt 2",
            "Price": "$102.15",
            "Rating": "3.9 / 5",
            "Colors": "3 Colors",
            "Size": "M",
            "Gender": "Women",
            "Timestamp": "2025-02-10T13:54:32.640365",
        },
        {
            "Title": "Unknown Product",
            "Price": "$100.00",
            "Rating": "Invalid Rating / 5",
            "Colors": "5 Colors",
            "Size": "M",
            "Gender": "Men",
            "Timestamp": "2025-02-10T13:54:32.640365",
        },
        {
            "Title": "Hoodie 3",
            "Price": None,
            "Rating": "4.8 / 5",
            "Colors": "3 Colors",
            "Size": "L",
            "Gender": "Unisex",
            "Timestamp": "2025-02-10T13:54:32.640460",
        },
    ]

    dataframe = transform_data(raw_data)

    assert len(dataframe) == 1
    assert dataframe.iloc[0]["Title"] == "T-shirt 2"
    assert dataframe.iloc[0]["Price"] == 1634400.0


def test_transform_data_returns_dataframe_with_expected_dtypes():
    """Memastikan DataFrame hasil transformasi memiliki dtype sesuai spesifikasi."""
    raw_data = [
        {
            "Title": "Hoodie 3",
            "Price": "$496.88",
            "Rating": "4.8 / 5",
            "Colors": "3 Colors",
            "Size": "L",
            "Gender": "Unisex",
            "Timestamp": "2025-02-10T13:54:32.640460",
        }
    ]

    dataframe = transform_data(raw_data)

    assert isinstance(dataframe, pd.DataFrame)
    assert dataframe["Title"].dtype == "object"
    assert dataframe["Price"].dtype == "float64"
    assert dataframe["Rating"].dtype == "float64"
    assert dataframe["Colors"].dtype == "int64"
    assert dataframe["Size"].dtype == "object"
    assert dataframe["Gender"].dtype == "object"
    assert dataframe["Timestamp"].dtype == "object"


def test_transform_data_accepts_lowercase_timestamp_column():
    """Memastikan kolom timestamp lowercase otomatis diubah ke Timestamp."""
    raw_data = [
        {
            "Title": "Outerwear 5",
            "Price": "$321.59",
            "Rating": "3.5 / 5",
            "Colors": "3 Colors",
            "Size": "XXL",
            "Gender": "Women",
            "timestamp": "2025-02-10T13:54:32.640648",
        }
    ]

    dataframe = transform_data(raw_data)

    assert "Timestamp" in dataframe.columns
    assert dataframe.iloc[0]["Timestamp"] == "2025-02-10T13:54:32.640648"


def test_transform_data_handles_empty_input():
    """Memastikan input kosong menghasilkan DataFrame kosong yang valid."""
    dataframe = transform_data([])
    empty_dataframe = create_empty_dataframe()

    assert list(dataframe.columns) == list(empty_dataframe.columns)
    assert dataframe.empty


def test_transform_data_returns_empty_dataframe_when_unexpected_error_occurs(monkeypatch):
    """Memastikan transform_data aman saat terjadi error tak terduga."""
    def mock_clean_title(value):
        raise RuntimeError("clean title failed")

    monkeypatch.setattr(transform_module, "clean_title", mock_clean_title)

    dataframe = transform_data([{"Title": "Produk"}])

    assert dataframe.empty
