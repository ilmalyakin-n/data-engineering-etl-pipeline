"""Titik masuk untuk menjalankan alur ETL pipeline proyek."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from utils.extract import scrape_main
from utils.load import save_to_csv, save_to_google_sheets, save_to_postgresql
from utils.transform import transform_data


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(env_path: Path | None = None) -> None:
    """Memuat pasangan KEY=VALUE dari file .env ke environment variable."""
    try:
        target_path = env_path or (BASE_DIR / ".env")
        if not target_path.exists():
            logging.warning("File .env tidak ditemukan di %s", target_path)
            return

        for line in target_path.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as exc:
        logging.error("Gagal memuat file .env: %s", exc)


def get_postgresql_config() -> dict:
    """Membangun konfigurasi PostgreSQL dari environment variable atau nilai default."""
    try:
        return {
            "host": os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost")),
            "port": os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "fashion_studio")),
            "user": os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres")),
            "password": os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres")),
            "table": os.getenv("DB_TABLE", os.getenv("POSTGRES_TABLE", "fashion_products")),
        }
    except Exception as exc:
        logging.error("Gagal membangun konfigurasi PostgreSQL: %s", exc)
        return {
            "host": "localhost",
            "port": "5432",
            "database": "fashion_studio",
            "user": "postgres",
            "password": "postgres",
            "table": "fashion_products",
        }


def run_load_stage(dataframe) -> dict:
    """Menjalankan seluruh proses load dan tetap melanjutkan saat salah satu target gagal."""
    load_results = {}

    csv_path = BASE_DIR / "products.csv"
    credentials_value = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "google-sheets-api.json")
    credentials_path = Path(credentials_value)
    if not credentials_path.is_absolute():
        credentials_path = BASE_DIR / credentials_value

    spreadsheet_name = os.getenv(
        "SPREADSHEET_NAME",
        os.getenv("GOOGLE_SHEETS_NAME", "Fashion Studio Products"),
    )
    db_config = get_postgresql_config()

    load_jobs = [
        ("csv", lambda: save_to_csv(dataframe, str(csv_path))),
        (
            "google_sheets",
            lambda: save_to_google_sheets(
                dataframe,
                spreadsheet_name=spreadsheet_name,
                credentials_file=str(credentials_path),
            ),
        ),
        ("postgresql", lambda: save_to_postgresql(dataframe, db_config=db_config)),
    ]

    for target_name, load_function in load_jobs:
        try:
            logging.info("Memulai load ke %s.", target_name)
            load_results[target_name] = load_function()

            if load_results[target_name]:
                logging.info("Load ke %s berhasil.", target_name)
            else:
                logging.warning("Load ke %s gagal.", target_name)
        except Exception as exc:
            load_results[target_name] = False
            logging.error("Terjadi error saat load ke %s: %s", target_name, exc)

    return load_results


def run_pipeline() -> dict | None:
    """Menjalankan ETL pipeline secara berurutan dari extract hingga load."""
    try:
        load_env_file()

        logging.info("Tahap extract dimulai.")
        raw_data = scrape_main()
        logging.info("Tahap extract selesai dengan %s data mentah.", len(raw_data))

        logging.info("Tahap transform dimulai.")
        transformed_data = transform_data(raw_data)
        logging.info(
            "Tahap transform selesai dengan %s data bersih.", len(transformed_data)
        )

        if transformed_data.empty:
            logging.warning("Data hasil transform kosong, proses load tetap dijalankan.")

        logging.info("Tahap load dimulai.")
        load_results = run_load_stage(transformed_data)
        logging.info("Tahap load selesai dengan hasil: %s", load_results)

        return load_results
    except Exception as exc:
        logging.error("Pipeline ETL gagal dijalankan: %s", exc)
        return None


if __name__ == "__main__":
    run_pipeline()
