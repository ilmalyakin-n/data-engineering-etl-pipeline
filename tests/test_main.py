"""Unit test untuk memvalidasi alur pipeline pada main.py."""

from __future__ import annotations

import pandas as pd

import main


def test_get_postgresql_config_reads_environment(monkeypatch):
    """Memastikan konfigurasi PostgreSQL dibaca dari environment variable."""
    monkeypatch.setenv("POSTGRES_HOST", "db-host")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "etl_db")
    monkeypatch.setenv("POSTGRES_USER", "etl_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "etl_pass")
    monkeypatch.setenv("POSTGRES_TABLE", "etl_table")

    config = main.get_postgresql_config()

    assert config == {
        "host": "db-host",
        "port": "5433",
        "database": "etl_db",
        "user": "etl_user",
        "password": "etl_pass",
        "table": "etl_table",
    }


def test_run_load_stage_continues_when_one_target_fails(monkeypatch):
    """Memastikan semua target load tetap diproses walau ada satu yang gagal."""
    calls = []

    monkeypatch.setattr(main, "save_to_csv", lambda df, filename: calls.append("csv") or True)
    monkeypatch.setattr(
        main,
        "save_to_google_sheets",
        lambda df, spreadsheet_name, credentials_file: calls.append("google") or False,
    )
    monkeypatch.setattr(
        main, "save_to_postgresql", lambda df, db_config: calls.append("postgres") or True
    )
    monkeypatch.setattr(main, "get_postgresql_config", lambda: {"host": "localhost"})

    results = main.run_load_stage(dataframe=[])

    assert calls == ["csv", "google", "postgres"]
    assert results == {"csv": True, "google_sheets": False, "postgresql": True}


def test_run_pipeline_runs_extract_transform_and_load(monkeypatch):
    """Memastikan pipeline utama berjalan berurutan dan mengembalikan hasil load."""
    execution_order = []

    monkeypatch.setattr(
        main,
        "scrape_main",
        lambda: execution_order.append("extract") or [{"Title": "T-shirt 2"}],
    )
    monkeypatch.setattr(
        main,
        "transform_data",
        lambda raw_data: execution_order.append("transform")
        or pd.DataFrame([{"Title": "T-shirt 2"}]),
    )
    monkeypatch.setattr(
        main,
        "run_load_stage",
        lambda dataframe: execution_order.append("load")
        or {"csv": True, "google_sheets": True, "postgresql": True},
    )

    result = main.run_pipeline()

    assert execution_order == ["extract", "transform", "load"]
    assert result == {"csv": True, "google_sheets": True, "postgresql": True}


def test_run_load_stage_marks_target_false_when_exception_happens(monkeypatch):
    """Memastikan exception pada satu target load tidak menghentikan target lain."""
    dataframe = pd.DataFrame([{"Title": "T-shirt 2"}])
    calls = []

    def failing_csv(df, filename):
        calls.append("csv")
        raise RuntimeError("csv failed")

    monkeypatch.setattr(main, "save_to_csv", failing_csv)
    monkeypatch.setattr(
        main,
        "save_to_google_sheets",
        lambda df, spreadsheet_name, credentials_file: calls.append("google") or True,
    )
    monkeypatch.setattr(
        main, "save_to_postgresql", lambda df, db_config: calls.append("postgres") or True
    )
    monkeypatch.setattr(main, "get_postgresql_config", lambda: {"host": "localhost"})

    results = main.run_load_stage(dataframe)

    assert calls == ["csv", "google", "postgres"]
    assert results["csv"] is False
    assert results["google_sheets"] is True
    assert results["postgresql"] is True


def test_run_pipeline_handles_empty_transformed_dataframe(monkeypatch):
    """Memastikan pipeline tetap menjalankan load saat hasil transform kosong."""
    monkeypatch.setattr(main, "scrape_main", lambda: [{"Title": "T-shirt 2"}])
    monkeypatch.setattr(main, "transform_data", lambda raw_data: pd.DataFrame())
    monkeypatch.setattr(
        main,
        "run_load_stage",
        lambda dataframe: {"csv": True, "google_sheets": False, "postgresql": False},
    )

    result = main.run_pipeline()

    assert result == {"csv": True, "google_sheets": False, "postgresql": False}


def test_run_pipeline_returns_none_when_pipeline_fails(monkeypatch):
    """Memastikan run_pipeline mengembalikan None ketika terjadi error fatal."""
    def mock_scrape():
        raise RuntimeError("extract failed")

    monkeypatch.setattr(main, "scrape_main", mock_scrape)

    result = main.run_pipeline()

    assert result is None
