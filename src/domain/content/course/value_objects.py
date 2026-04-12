from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from src.domain.errors import InvariantViolationError

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


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


@dataclass(frozen=True, slots=True)
class CourseSchedule:
    """
    Расписание курса.

    :param starts_at: Дата и время старта курса.
    :type starts_at: datetime
    :param duration_days: Продолжительность в днях.
    :type duration_days: int
    """

    starts_at: datetime
    duration_days: int
    enrollment_opens_at: datetime | None = None
    enrollment_closes_at: datetime | None = None
    access_ttl_days: int | None = None
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        if self.duration_days <= 0:
            raise InvariantViolationError("duration_days должен быть больше 0")
        if self.access_ttl_days is not None and self.access_ttl_days <= 0:
            raise InvariantViolationError("access_ttl_days должен быть больше 0")
        if not self.timezone.strip():
            raise InvariantViolationError("timezone обязателен")
        if (
            self.enrollment_opens_at is not None
            and self.enrollment_closes_at is not None
            and self.enrollment_opens_at > self.enrollment_closes_at
        ):
            raise InvariantViolationError(
                "enrollment_opens_at не может быть позже enrollment_closes_at"
            )


@dataclass(frozen=True, slots=True)
class CoursePricing:
    """
    Ценовые параметры курса.

    :param price: Цена курса.
    :type price: float
    :param currency: Код валюты ISO-4217.
    :type currency: str
    """

    price: float = 0.0
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.price < 0:
            raise InvariantViolationError("price не может быть отрицательной")
        if not _CURRENCY_PATTERN.fullmatch(self.currency):
            raise InvariantViolationError(
                "currency должен быть ISO-4217 (3 заглавные буквы)"
            )


@dataclass(frozen=True, slots=True)
class CourseAudience:
    """
    Аудиторные параметры курса.

    :param language: Язык курса.
    :type language: str
    :param level: Уровень курса.
    :type level: str
    :param age_min: Минимальный возраст.
    :type age_min: int | None
    :param age_max: Максимальный возраст.
    :type age_max: int | None
    :param max_students: Максимум студентов в потоке/курсе.
    :type max_students: int | None
    """

    language: str = "ru"
    level: str = "beginner"
    age_min: int | None = None
    age_max: int | None = None
    max_students: int | None = None

    def __post_init__(self) -> None:
        if not self.language.strip():
            raise InvariantViolationError("language обязателен")
        if not self.level.strip():
            raise InvariantViolationError("level обязателен")
        if self.age_min is not None and self.age_min < 0:
            raise InvariantViolationError("age_min не может быть отрицательным")
        if self.age_max is not None and self.age_max < 0:
            raise InvariantViolationError("age_max не может быть отрицательным")
        if (
            self.age_min is not None
            and self.age_max is not None
            and self.age_min > self.age_max
        ):
            raise InvariantViolationError("age_min не может быть больше age_max")
        if self.max_students is not None and self.max_students <= 0:
            raise InvariantViolationError("max_students должен быть больше 0")


@dataclass(frozen=True, slots=True)
class CourseDeliverySettings:
    """
    Настройки представления и live-доставки курса.

    :param tags: Теги курса.
    :type tags: tuple[str, ...]
    :param cover_image_url: URL обложки.
    :type cover_image_url: str | None
    :param is_live_enabled: Флаг live-режима.
    :type is_live_enabled: bool
    :param live_room_template_id: Идентификатор шаблона live-комнаты.
    :type live_room_template_id: str | None
    """

    tags: tuple[str, ...] = ()
    cover_image_url: str | None = None
    is_live_enabled: bool = False
    live_room_template_id: str | None = None

    def __post_init__(self) -> None:
        normalized_tags = [tag.strip() for tag in self.tags if tag.strip()]
        if len(set(normalized_tags)) != len(normalized_tags):
            raise InvariantViolationError("tags не должны содержать дубликаты")
        if self.cover_image_url:
            parsed = urlparse(self.cover_image_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise InvariantViolationError(
                    "cover_image_url должен быть корректным http/https URL"
                )
        if self.is_live_enabled and not (
            self.live_room_template_id and self.live_room_template_id.strip()
        ):
            raise InvariantViolationError(
                "live_room_template_id обязателен при is_live_enabled=true"
            )
