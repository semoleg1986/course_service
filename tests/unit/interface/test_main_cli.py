from __future__ import annotations

from types import SimpleNamespace

from src.interface.http import main


def test_dispatch_outbox_cli_invokes_runtime_dispatcher(monkeypatch) -> None:
    calls: list[int] = []

    def _dispatch(*, limit: int = 100) -> None:
        calls.append(limit)

    monkeypatch.setattr(
        main,
        "build_runtime",
        lambda: SimpleNamespace(bonus_outbox_dispatcher=_dispatch),
    )

    exit_code = main.main(["dispatch-outbox", "--limit", "19"])

    assert exit_code == 0
    assert calls == [19]
