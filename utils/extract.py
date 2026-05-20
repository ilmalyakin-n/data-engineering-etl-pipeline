"""Fungsi-fungsi untuk mengekstrak data produk dari sumber web."""

from __future__ import annotations

from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://fashion-studio.dicoding.dev"
TOTAL_PAGES = 50
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}


def fetch_page(session: requests.Session, page_number: int) -> BeautifulSoup | None:
    """Mengambil satu halaman katalog dan mengembalikan objek BeautifulSoup."""
    try:
        url = f"{BASE_URL}/" if page_number == 1 else f"{BASE_URL}/page{page_number}"
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as exc:
        print(f"Request error saat mengambil halaman {page_number}: {exc}")
        return None
    except Exception as exc:
        print(f"Error tak terduga saat mengambil halaman {page_number}: {exc}")
        return None


def extract_product_data(card) -> dict | None:
    """Mengekstrak data produk dari satu kartu produk HTML."""
    try:
        title_tag = card.select_one(".product-title")
        price_tag = card.select_one(".price")
        detail_texts = [
            detail.get_text(" ", strip=True) for detail in card.select(".product-details p")
        ]

        if title_tag is None or price_tag is None:
            raise ValueError("Struktur kartu produk tidak lengkap.")

        rating_text = next(
            (text for text in detail_texts if text.startswith("Rating:")),
            None,
        )
        colors_text = next(
            (
                text
                for text in detail_texts
                if "Colors" in text and not text.startswith("Rating:")
            ),
            None,
        )
        size_text = next(
            (text for text in detail_texts if text.startswith("Size:")),
            None,
        )
        gender_text = next(
            (text for text in detail_texts if text.startswith("Gender:")),
            None,
        )

        if not all([rating_text, colors_text, size_text, gender_text]):
            raise ValueError("Detail produk tidak lengkap.")

        rating = rating_text.replace("Rating:", "", 1).replace("\u2b50", "", 1).strip()
        size = size_text.replace("Size:", "", 1).strip()
        gender = gender_text.replace("Gender:", "", 1).strip()

        return {
            "Title": title_tag.get_text(strip=True),
            "Price": price_tag.get_text(strip=True),
            "Rating": rating,
            "Colors": colors_text,
            "Size": size,
            "Gender": gender,
            "Timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except requests.exceptions.RequestException as exc:
        print(f"Request error saat memproses kartu produk: {exc}")
        return None
    except Exception as exc:
        print(f"Error tak terduga saat memproses kartu produk: {exc}")
        return None


def extract_page_products(soup: BeautifulSoup) -> list[dict]:
    """Mengambil semua data produk dari satu halaman katalog."""
    try:
        products = []
        cards = soup.select(".collection-card")

        for card in cards:
            product_data = extract_product_data(card)
            if product_data is not None:
                products.append(product_data)

        return products
    except requests.exceptions.RequestException as exc:
        print(f"Request error saat mengekstrak data halaman: {exc}")
        return []
    except Exception as exc:
        print(f"Error tak terduga saat mengekstrak data halaman: {exc}")
        return []


def scrape_main() -> list[dict]:
    """Melakukan scraping halaman 1-50 dan mengembalikan data sebagai list of dict."""
    try:
        products = []

        with requests.Session() as session:
            for page_number in range(1, TOTAL_PAGES + 1):
                soup = fetch_page(session, page_number)
                if soup is None:
                    continue

                products.extend(extract_page_products(soup))

        return products
    except requests.exceptions.RequestException as exc:
        print(f"Request error saat menjalankan scraping utama: {exc}")
        return []
    except Exception as exc:
        print(f"Error tak terduga saat menjalankan scraping utama: {exc}")
        return []
