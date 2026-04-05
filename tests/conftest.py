from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def force_inmemory_for_non_integration(request: pytest.FixtureRequest) -> None:
    """Фиксирует in-memory режим для обычных тестов, не затрагивая integration."""

    if request.node.get_closest_marker("integration"):
        return

    os.environ["COURSE_USE_INMEMORY"] = "1"
    os.environ.pop("COURSE_DATABASE_URL", None)
    os.environ["COURSE_AUTO_CREATE_SCHEMA"] = "0"
