from __future__ import annotations

from pathlib import Path


"""
Centralized filesystem paths used across GitHelp.

This module defines the main project directories so that scripts and modules
do not have to rebuild paths manually. Keeping paths here makes the project
structure easier to change later.
"""


# Root directory of the GitHelp repository.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Configuration files.
CONFIG_DIR = PROJECT_ROOT / "configs"

# Data directories.
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTRACTED_CODE_DOCS_DIR = DATA_DIR / "extracted_code_docs"

# Index directories.
INDEXES_DIR = DATA_DIR / "indexes"
MMORE_INDEX_DIR = INDEXES_DIR / "mmore"