# Advanced Fashion ETL Pipeline

An advanced ETL (Extract, Transform, Load) pipeline project built using Python to automate fashion product data collection, transformation, validation, and storage into multiple repositories.

This project was developed as the final submission for the Dicoding course:

> Belajar Fundamental Pemrosesan Data

and successfully achieved the **Advanced Criteria (5 Stars)**.

---

# Project Overview

This project implements a complete ETL workflow:

1. **Extract**
   - Scrape fashion product data from a website
   - Collect product information automatically from multiple pages

2. **Transform**
   - Clean invalid and duplicate data
   - Standardize formats and data types
   - Convert currency from USD to IDR
   - Improve overall data quality

3. **Load**
   - Store cleaned data into:
     - CSV
     - Google Sheets
     - PostgreSQL

4. **Testing**
   - Unit testing for every ETL module
   - High test coverage implementation

---

# Features

## Extract Process
- Web scraping using Python
- Crawl data from pages 1–50
- Extract:
  - Title
  - Price
  - Rating
  - Colors
  - Size
  - Gender
- Timestamp generation
- Error handling implementation

## Transform Process
- Remove:
  - Null values
  - Invalid values
  - Duplicate data
- Convert:
  - USD → IDR (Rp16.000)
  - Rating → float
  - Colors → integer
- Standardize text formatting
- Data type validation

## Load Process
Data stored into:
- CSV file
- Google Sheets
- PostgreSQL database

Each load function includes error handling.

---

# Project Structure

```bash
ETL PIPELINE SEDERHANA/
│
├── tests/
│   ├── test_extract.py
│   ├── test_load.py
│   ├── test_main.py
│   └── test_transform.py
│
├── utils/
│   ├── extract.py
│   ├── load.py
│   └── transform.py
│
├── google-sheets-api.json
├── main.py
├── products.csv
├── requirements.txt
└── submission.txt
```

---

# Technologies Used

- Python
- Pandas
- BeautifulSoup4
- Requests
- PostgreSQL
- Google Sheets API
- Pytest

---

# Data Quality Validation

The transformed dataset guarantees:

- No duplicate data
- No null values
- No invalid products
- Proper data types
- Clean formatting
- Consistent schema

---

# Unit Testing

This project includes unit testing for:

- Extract module
- Transform module
- Load module
- Main ETL process

Test coverage successfully achieved:
- **80%+ coverage (Advanced Criteria)**

---

# Installation

Clone repository:

```bash
git clone https://github.com/your-username/advanced-fashion-etl-pipeline.git
```

Move into project directory:

```bash
cd advanced-fashion-etl-pipeline
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# How to Run

Run ETL pipeline:

```bash
python main.py
```

Run unit tests:

```bash
pytest
```

---

# Example Output

| Title | Price | Rating | Colors | Size | Gender | Timestamp |
|------|------|------|------|------|------|------|
| Hoodie Basic | 320000 | 4.8 | 3 | M | Men | 2026-05-20 |

---

# Reviewer Feedback Improvements

This project also received several improvement suggestions from reviewers for future enhancement:

- Using `.env` with `python-dotenv`
- Migrating Google Sheets integration to `gspread`
- Applying PEP 8 style guide
- Adding docstring documentation
- Replacing `print()` with Python `logging`

These suggestions are valuable references for improving code maintainability and production readiness.

---

# Learning Outcomes

Through this project, I learned:

- Modular ETL architecture
- Web scraping automation
- Data cleaning & preprocessing
- Data validation
- Multi-storage integration
- Error handling
- Unit testing
- Test coverage implementation
- Writing maintainable Python code

---

# Author

**Ilmal**  
Information Systems Student  
Universitas Al-Ghifari

---

# Certificate

This project was created as part of the Dicoding Data Processing Fundamentals course submission.
