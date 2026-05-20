"""Fungsi-fungsi untuk membersihkan dan mentransformasi data produk."""

from __future__ import annotations

import re

import pandas as pd

USD_TO_IDR_RATE = 16000.0
VALID_GENDERS = {"Men", "Women", "Unisex"}
OUTPUT_COLUMNS = [
    "Title",
    "Price",
    "Rating",
    "Colors",
    "Size",
    "Gender",
    "Timestamp",
]


def create_empty_dataframe() -> pd.DataFrame:
    """Membuat DataFrame kosong dengan kolom dan tipe data akhir yang diharapkan."""
    try:
        dataframe = pd.DataFrame(columns=OUTPUT_COLUMNS)
        return dataframe.astype(
            {
                "Title": "object",
                "Price": "float64",
                "Rating": "float64",
                "Colors": "int64",
                "Size": "object",
                "Gender": "object",
                "Timestamp": "object",
            }
        )
    except Exception as exc:
        print(f"Error tak terduga saat membuat DataFrame kosong: {exc}")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)


def clean_title(value) -> str | None:
    """Membersihkan nilai title dan menandai title invalid sebagai None."""
    try:
        if value is None or pd.isna(value):
            return None

        title = str(value).strip()
        if not title or title == "Unknown Product":
            return None

        return title
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan title: {exc}")
        return None


def convert_price_to_rupiah(value) -> float | None:
    """Mengonversi harga USD ke rupiah dan mengembalikan nilai float."""
    try:
        if value is None or pd.isna(value):
            return None

        price_text = str(value).strip()
        if not price_text or price_text == "Price Unavailable":
            return None

        price_match = re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", ""))
        if price_match is None:
            return None

        usd_price = float(price_match.group(1))
        return float(usd_price * USD_TO_IDR_RATE)
    except Exception as exc:
        print(f"Error tak terduga saat mengonversi price: {exc}")
        return None


def clean_rating(value) -> float | None:
    """Membersihkan nilai rating dan mengubahnya menjadi float."""
    try:
        if value is None or pd.isna(value):
            return None

        rating_text = str(value).strip()
        invalid_patterns = ("Invalid Rating", "Not Rated", "Price Unavailable")

        if not rating_text or any(pattern in rating_text for pattern in invalid_patterns):
            return None

        rating_match = re.search(r"(\d+(?:\.\d+)?)", rating_text)
        if rating_match is None:
            return None

        return float(rating_match.group(1))
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan rating: {exc}")
        return None


def clean_colors(value) -> int | None:
    """Membersihkan nilai colors dan mengubahnya menjadi integer."""
    try:
        if value is None or pd.isna(value):
            return None

        colors_text = str(value).strip()
        if not colors_text or "Rating:" in colors_text:
            return None

        colors_match = re.search(r"(\d+)", colors_text)
        if colors_match is None:
            return None

        return int(colors_match.group(1))
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan colors: {exc}")
        return None


def clean_size(value) -> str | None:
    """Membersihkan nilai size dan memastikan hasil akhirnya berupa string ukuran."""
    try:
        if value is None or pd.isna(value):
            return None

        size = str(value).replace("Size:", "", 1).strip()
        valid_sizes = {"S", "M", "L", "XL", "XXL"}

        if size not in valid_sizes:
            return None

        return size
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan size: {exc}")
        return None


def clean_gender(value) -> str | None:
    """Membersihkan nilai gender dan memastikan nilainya valid."""
    try:
        if value is None or pd.isna(value):
            return None

        gender = str(value).replace("Gender:", "", 1).strip()
        if gender not in VALID_GENDERS:
            return None

        return gender
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan gender: {exc}")
        return None


def clean_timestamp(value) -> str | None:
    """Menjaga timestamp tetap dalam format string ISO 8601 jika tersedia."""
    try:
        if value is None or pd.isna(value):
            return None

        timestamp = str(value).strip()
        return timestamp or None
    except Exception as exc:
        print(f"Error tak terduga saat membersihkan timestamp: {exc}")
        return None


def transform_data(raw_data: list[dict]) -> pd.DataFrame:
    """Mengubah list of dict hasil scraping menjadi DataFrame yang bersih."""
    try:
        if not raw_data:
            return create_empty_dataframe()

        dataframe = pd.DataFrame(raw_data).copy()

        if "timestamp" in dataframe.columns and "Timestamp" not in dataframe.columns:
            dataframe = dataframe.rename(columns={"timestamp": "Timestamp"})

        for column in OUTPUT_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = None

        dataframe = dataframe[OUTPUT_COLUMNS]

        dataframe["Title"] = dataframe["Title"].apply(clean_title)
        dataframe["Price"] = dataframe["Price"].apply(convert_price_to_rupiah)
        dataframe["Rating"] = dataframe["Rating"].apply(clean_rating)
        dataframe["Colors"] = dataframe["Colors"].apply(clean_colors)
        dataframe["Size"] = dataframe["Size"].apply(clean_size)
        dataframe["Gender"] = dataframe["Gender"].apply(clean_gender)
        dataframe["Timestamp"] = dataframe["Timestamp"].apply(clean_timestamp)

        dataframe = dataframe.dropna()
        dataframe = dataframe.drop_duplicates(
            subset=["Title", "Price", "Rating", "Colors", "Size", "Gender"]
        )

        dataframe = dataframe.astype(
            {
                "Title": "object",
                "Price": "float64",
                "Rating": "float64",
                "Colors": "int64",
                "Size": "object",
                "Gender": "object",
                "Timestamp": "object",
            }
        )

        return dataframe
    except Exception as exc:
        print(f"Error tak terduga saat mentransformasi data: {exc}")
        return create_empty_dataframe()
