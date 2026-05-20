"""Unit test untuk memvalidasi proses ekstraksi data."""

from __future__ import annotations

from bs4 import BeautifulSoup
import requests

from utils import extract


SAMPLE_PAGE_HTML = """
<html>
  <body>
    <div class="collection-card">
      <div class="product-details">
        <h3 class="product-title">T-shirt 2</h3>
        <span class="price">$102.15</span>
        <p>Rating: ⭐ 3.9 / 5</p>
        <p>3 Colors</p>
        <p>Size: M</p>
        <p>Gender: Women</p>
      </div>
    </div>
  </body>
</html>
"""

SAMPLE_UNAVAILABLE_PRICE_HTML = """
<html>
  <body>
    <div class="collection-card">
      <div class="product-details">
        <h3 class="product-title">Pants 16</h3>
        <p class="price">Price Unavailable</p>
        <p>Rating: Not Rated</p>
        <p>8 Colors</p>
        <p>Size: S</p>
        <p>Gender: Men</p>
      </div>
    </div>
  </body>
</html>
"""


def test_scrape_main_returns_list_of_dict(monkeypatch):
    """Memastikan scrape_main mengembalikan list berisi dict produk."""
    sample_soup = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser")

    monkeypatch.setattr(extract, "TOTAL_PAGES", 2)
    monkeypatch.setattr(extract, "fetch_page", lambda session, page_number: sample_soup)

    products = extract.scrape_main()

    assert isinstance(products, list)
    assert products
    assert all(isinstance(product, dict) for product in products)


def test_scrape_main_dict_contains_expected_keys(monkeypatch):
    """Memastikan setiap hasil scraping memiliki key sesuai spesifikasi."""
    sample_soup = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser")
    expected_keys = {
        "Title",
        "Price",
        "Rating",
        "Colors",
        "Size",
        "Gender",
        "Timestamp",
    }

    monkeypatch.setattr(extract, "TOTAL_PAGES", 1)
    monkeypatch.setattr(extract, "fetch_page", lambda session, page_number: sample_soup)

    products = extract.scrape_main()

    assert set(products[0].keys()) == expected_keys


def test_fetch_page_returns_beautifulsoup_when_request_succeeds():
    """Memastikan fetch_page mengembalikan BeautifulSoup saat request berhasil."""

    class FakeResponse:
        text = SAMPLE_PAGE_HTML

        def raise_for_status(self):
            return None

    class FakeSession:
        def get(self, url, headers=None, timeout=None):
            return FakeResponse()

    soup = extract.fetch_page(FakeSession(), 1)

    assert isinstance(soup, BeautifulSoup)
    assert soup.select_one(".product-title").get_text(strip=True) == "T-shirt 2"


def test_fetch_page_returns_none_when_request_fails(monkeypatch):
    """Memastikan kegagalan akses website ditangani dan menghasilkan list kosong."""
    monkeypatch.setattr(extract, "TOTAL_PAGES", 1)

    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Website unavailable")

    monkeypatch.setattr(requests.sessions.Session, "get", mock_get)

    products = extract.scrape_main()

    assert products == []


def test_extract_product_data_returns_none_for_invalid_card():
    """Memastikan kartu produk yang tidak lengkap dikembalikan sebagai None."""
    invalid_card_html = """
    <div class="collection-card">
      <div class="product-details">
        <h3 class="product-title">Produk Rusak</h3>
      </div>
    </div>
    """
    card = BeautifulSoup(invalid_card_html, "html.parser").select_one(".collection-card")

    product = extract.extract_product_data(card)

    assert product is None


def test_extract_product_data_returns_expected_values_for_valid_card():
    """Memastikan data kartu valid diekstrak dengan field yang benar."""
    card = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser").select_one(".collection-card")

    product = extract.extract_product_data(card)

    assert product["Title"] == "T-shirt 2"
    assert product["Price"] == "$102.15"
    assert product["Rating"] == "3.9 / 5"
    assert product["Colors"] == "3 Colors"
    assert product["Size"] == "M"
    assert product["Gender"] == "Women"
    assert "Timestamp" in product


def test_extract_page_products_returns_empty_list_for_invalid_soup():
    """Memastikan extract_page_products aman saat menerima input tidak valid."""
    products = extract.extract_page_products(None)

    assert products == []


def test_extract_page_products_returns_products_for_valid_soup():
    """Memastikan semua kartu pada halaman valid berhasil diekstrak."""
    soup = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser")

    products = extract.extract_page_products(soup)

    assert len(products) == 1
    assert products[0]["Title"] == "T-shirt 2"


def test_extract_product_data_handles_price_unavailable_card():
    """Memastikan kartu dengan price unavailable tetap diekstrak ke field yang tepat."""
    card = BeautifulSoup(
        SAMPLE_UNAVAILABLE_PRICE_HTML, "html.parser"
    ).select_one(".collection-card")

    product = extract.extract_product_data(card)

    assert product["Price"] == "Price Unavailable"
    assert product["Rating"] == "Not Rated"
    assert product["Colors"] == "8 Colors"
    assert product["Size"] == "S"
    assert product["Gender"] == "Men"
