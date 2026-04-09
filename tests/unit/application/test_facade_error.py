from __future__ import annotations

import pytest

from src.application.facade.application_facade import ApplicationFacade


class _UnknownQuery:
    pass


def test_facade_raises_lookup_error_for_unknown_query() -> None:
    facade = ApplicationFacade()
    with pytest.raises(LookupError):
        facade.query(_UnknownQuery())
