"""ASGI entrypoint."""

from __future__ import annotations

import argparse

from src.infrastructure.di.composition import build_runtime
from src.interface.http.app import create_app

app = create_app()


def main(argv: list[str] | None = None) -> int:
    """CLI helper для dispatch outbox и локальных ops-задач."""

    parser = argparse.ArgumentParser(prog="course_service")
    subparsers = parser.add_subparsers(dest="command")

    dispatch = subparsers.add_parser(
        "dispatch-outbox",
        help="Доставить pending outbox-события course_service",
    )
    dispatch.add_argument("--limit", type=int, default=100)

    args = parser.parse_args(argv)
    if args.command != "dispatch-outbox":
        parser.print_help()
        return 0

    runtime = build_runtime()
    runtime.bonus_outbox_dispatcher(limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
