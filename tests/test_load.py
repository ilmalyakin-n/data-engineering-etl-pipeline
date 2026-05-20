"""Unit test untuk memvalidasi proses pemuatan data."""

from __future__ import annotations

import sys
import types

import pandas as pd

from utils import load


def create_sample_dataframe() -> pd.DataFrame:
    """Membuat DataFrame contoh untuk pengujian proses load."""
    return pd.DataFrame(
        [
            {
                "Title": "T-shirt 2",
                "Price": 1634400.0,
                "Rating": 3.9,
                "Colors": 3,
                "Size": "M",
                "Gender": "Women",
                "Timestamp": "2025-02-10T13:54:32.640365",
            }
        ]
    )


def test_save_to_csv_creates_csv_file(tmp_path):
    """Memastikan save_to_csv berhasil membuat file CSV."""
    dataframe = create_sample_dataframe()
    output_file = tmp_path / "products.csv"

    result = load.save_to_csv(dataframe, str(output_file))

    assert result is True
    assert output_file.exists()


def test_save_to_csv_returns_false_when_write_fails(monkeypatch, tmp_path):
    """Memastikan save_to_csv mengembalikan False saat penyimpanan gagal."""
    dataframe = create_sample_dataframe()
    output_file = tmp_path / "products.csv"

    def mock_to_csv(*args, **kwargs):
        raise OSError("write failed")

    monkeypatch.setattr(pd.DataFrame, "to_csv", mock_to_csv)

    result = load.save_to_csv(dataframe, str(output_file))

    assert result is False


def test_save_to_google_sheets_with_mocked_gspread(monkeypatch, tmp_path):
    """Memastikan save_to_google_sheets berhasil dengan dependency yang dimock."""
    dataframe = create_sample_dataframe()
    credentials_file = tmp_path / "google-sheets-api.json"
    credentials_file.write_text('{"type": "service_account"}', encoding="utf-8")

    updates = []

    class FakeWorksheet:
        def clear(self):
            return None

        def update(self, range_name=None, values=None):
            updates.append((range_name, values))

    class FakeSpreadsheet:
        def __init__(self):
            self.sheet1 = FakeWorksheet()

    class SpreadsheetNotFound(Exception):
        """Exception palsu untuk meniru gspread.SpreadsheetNotFound."""

    fake_client = types.SimpleNamespace(open=lambda name: FakeSpreadsheet())

    fake_gspread = types.ModuleType("gspread")
    fake_gspread.SpreadsheetNotFound = SpreadsheetNotFound
    fake_gspread.authorize = lambda credentials: fake_client

    fake_service_account = types.ModuleType("oauth2client.service_account")

    class FakeCredentials:
        @staticmethod
        def from_json_keyfile_name(filename, scope):
            return {"filename": filename, "scope": scope}

    fake_service_account.ServiceAccountCredentials = FakeCredentials

    fake_oauth2client = types.ModuleType("oauth2client")

    monkeypatch.setitem(sys.modules, "gspread", fake_gspread)
    monkeypatch.setitem(sys.modules, "oauth2client", fake_oauth2client)
    monkeypatch.setitem(sys.modules, "oauth2client.service_account", fake_service_account)

    result = load.save_to_google_sheets(
        dataframe,
        spreadsheet_name="Fashion Studio Products",
        credentials_file=str(credentials_file),
    )

    assert result is True
    assert updates
    assert updates[0][0] == "A1"
    assert updates[0][1][0] == dataframe.columns.tolist()


def test_save_to_google_sheets_returns_false_when_credentials_missing():
    """Memastikan save_to_google_sheets gagal saat file kredensial tidak ada."""
    dataframe = create_sample_dataframe()

    result = load.save_to_google_sheets(
        dataframe,
        spreadsheet_name="Fashion Studio Products",
        credentials_file="missing-google-sheets-api.json",
    )

    assert result is False


def test_save_to_postgresql_with_mocked_psycopg2(monkeypatch):
    """Memastikan save_to_postgresql berhasil dengan psycopg2 yang dimock."""
    dataframe = create_sample_dataframe()
    executed_queries = []
    inserted_records = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query):
            executed_queries.append(query)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

        def close(self):
            return None

    class FakeSQLQuery:
        def __init__(self, query):
            self.query = query

        def format(self, **kwargs):
            return self

        def as_string(self, connection):
            return self.query

    fake_sql_module = types.SimpleNamespace(
        SQL=lambda query: FakeSQLQuery(query),
        Identifier=lambda name: name,
    )

    fake_extras_module = types.ModuleType("psycopg2.extras")

    def fake_execute_batch(cursor, query, records):
        inserted_records.extend(records)
        executed_queries.append(query)

    fake_extras_module.execute_batch = fake_execute_batch

    fake_psycopg2 = types.ModuleType("psycopg2")
    fake_psycopg2.connect = lambda **kwargs: FakeConnection()
    fake_psycopg2.sql = fake_sql_module

    monkeypatch.setitem(sys.modules, "psycopg2", fake_psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.extras", fake_extras_module)

    result = load.save_to_postgresql(
        dataframe,
        {
            "host": "localhost",
            "port": "5432",
            "database": "fashion_studio",
            "user": "postgres",
            "password": "postgres",
            "table": "fashion_products",
        },
    )

    assert result is True
    assert inserted_records
    assert executed_queries


def test_save_to_postgresql_returns_false_when_connection_fails(monkeypatch):
    """Memastikan save_to_postgresql mengembalikan False saat koneksi gagal."""
    dataframe = create_sample_dataframe()

    fake_psycopg2 = types.ModuleType("psycopg2")

    def mock_connect(**kwargs):
        raise RuntimeError("database unavailable")

    fake_psycopg2.connect = mock_connect
    fake_psycopg2.sql = types.SimpleNamespace()

    monkeypatch.setitem(sys.modules, "psycopg2", fake_psycopg2)

    result = load.save_to_postgresql(
        dataframe,
        {
            "host": "localhost",
            "port": "5432",
            "database": "fashion_studio",
            "user": "postgres",
            "password": "postgres",
        },
    )

    assert result is False
