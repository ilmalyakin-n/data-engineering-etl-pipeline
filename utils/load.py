"""Fungsi-fungsi untuk menyimpan data hasil ETL ke repositori tujuan."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_to_csv(df: pd.DataFrame, filename: str = "products.csv") -> bool:
    """Menyimpan DataFrame ke file CSV dan mengembalikan status keberhasilan."""
    try:
        output_path = Path(filename)
        df.to_csv(output_path, index=False)
        return True
    except Exception as exc:
        print(f"Gagal menyimpan data ke CSV: {exc}")
        return False


def save_to_google_sheets(
    df: pd.DataFrame,
    spreadsheet_name: str,
    credentials_file: str = "google-sheets-api.json",
) -> bool:
    """Mengunggah DataFrame ke Google Sheets menggunakan service account."""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        credentials_path = Path(credentials_file)
        if not credentials_path.exists():
            raise FileNotFoundError(f"File kredensial tidak ditemukan: {credentials_file}")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            str(credentials_path), scope
        )
        client = gspread.authorize(credentials)

        try:
            if spreadsheet_name.startswith("http://") or spreadsheet_name.startswith("https://"):
                spreadsheet = client.open_by_url(spreadsheet_name)
            else:
                spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)

        worksheet = spreadsheet.sheet1
        worksheet.clear()

        sheet_ready_df = df.astype(object).where(pd.notna(df), "")
        rows = [sheet_ready_df.columns.tolist()] + sheet_ready_df.values.tolist()
        worksheet.update(range_name="A1", values=rows)
        return True
    except FileNotFoundError as exc:
        print(f"Gagal menyimpan data ke Google Sheets: {exc}")
        return False
    except ModuleNotFoundError as exc:
        print(f"Library Google Sheets belum tersedia: {exc}")
        return False
    except Exception as exc:
        print(f"Gagal terhubung atau mengunggah ke Google Sheets: {exc}")
        return False


def save_to_postgresql(df: pd.DataFrame, db_config: dict) -> bool:
    """Menyimpan DataFrame ke tabel PostgreSQL menggunakan konfigurasi koneksi."""
    connection = None
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extras import execute_batch

        connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )

        table_name = db_config.get("table", "fashion_products")

        with connection:
            with connection.cursor() as cursor:
                create_table_query = sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        title TEXT,
                        price DOUBLE PRECISION,
                        rating DOUBLE PRECISION,
                        colors INTEGER,
                        size TEXT,
                        gender TEXT,
                        timestamp TEXT
                    )
                    """
                ).format(table_name=sql.Identifier(table_name))
                cursor.execute(create_table_query)

                truncate_query = sql.SQL("TRUNCATE TABLE {table_name}").format(
                    table_name=sql.Identifier(table_name)
                )
                cursor.execute(truncate_query)

                records = [
                    (
                        row["Title"],
                        float(row["Price"]),
                        float(row["Rating"]),
                        int(row["Colors"]),
                        row["Size"],
                        row["Gender"],
                        row["Timestamp"],
                    )
                    for _, row in df.iterrows()
                ]

                if records:
                    insert_query = sql.SQL(
                        """
                        INSERT INTO {table_name}
                        (title, price, rating, colors, size, gender, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                    ).format(table_name=sql.Identifier(table_name))
                    execute_batch(
                        cursor,
                        insert_query.as_string(connection),
                        records,
                    )

        return True
    except ModuleNotFoundError as exc:
        print(f"Library PostgreSQL belum tersedia: {exc}")
        return False
    except Exception as exc:
        print(f"Gagal terhubung atau menyimpan ke PostgreSQL: {exc}")
        return False
    finally:
        if connection is not None:
            connection.close()
