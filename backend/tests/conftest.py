"""
tests/conftest.py
-----------------
Pytest configuration and environment overrides for unit tests.
"""
from __future__ import annotations

import os

# Force embedding provider to placeholder for unit tests to avoid network calls
os.environ["EMBEDDING_PROVIDER"] = "placeholder"

from app.core.config import settings
settings.EMBEDDING_PROVIDER = "placeholder"
