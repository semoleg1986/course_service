from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.errors import InvariantViolationError

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class CourseSlug:
    """
    SEO-friendly slug курса.

    :param value: Строковое значение slug.
    :type value: str
    :raises InvariantViolationError: Если формат slug невалиден.
    """

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_PATTERN.fullmatch(self.value):
            raise InvariantViolationError("Некорректный формат slug курса")


@dataclass(frozen=True, slots=True)
class SeoMetadata:
    """
    SEO-метаданные карточки курса.

    :param meta_title: Title страницы.
    :type meta_title: str
    :param meta_description: Meta description.
    :type meta_description: str
    :param canonical_url: Канонический URL (опционально).
    :type canonical_url: str | None
    :param robots: Политика индексации (`index`|`noindex`).
    :type robots: str
    :param og_image_url: OpenGraph изображение (опционально).
    :type og_image_url: str | None
    """

    meta_title: str
    meta_description: str
    canonical_url: str | None = None
    robots: str = "index"
    og_image_url: str | None = None

    def __post_init__(self) -> None:
        if not self.meta_title.strip():
            raise InvariantViolationError("meta_title обязателен")
        if not self.meta_description.strip():
            raise InvariantViolationError("meta_description обязателен")
        if len(self.meta_title) > 70:
            raise InvariantViolationError("meta_title слишком длинный")
        if len(self.meta_description) > 160:
            raise InvariantViolationError("meta_description слишком длинный")
        if self.robots not in {"index", "noindex"}:
            raise InvariantViolationError("robots должен быть index или noindex")
