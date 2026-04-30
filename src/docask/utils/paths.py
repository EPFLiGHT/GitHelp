from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTRACTED_CODE_DOCS_DIR = DATA_DIR / "extracted_code_docs"
INDEXES_DIR = DATA_DIR / "indexes"
MMORE_INDEX_DIR = INDEXES_DIR / "mmore"