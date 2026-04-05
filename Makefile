# ========================
# Requirements
# ========================

requirements: ## Скомпилировать requirements.in в requirements.txt
	pip-compile requirements.in

install: requirements ## Установить зависимости
	pip install -r requirements.txt

# ========================
# Test
# ========================

test: ## Запустить все тесты с подробным выводом
	pytest -v

test-integration: ## Запустить интеграционные тесты с Postgres
	COURSE_USE_INMEMORY=0 \
	COURSE_DATABASE_URL="$${COURSE_DATABASE_URL:-postgresql+psycopg://postgres:postgres@localhost:5432/course_service_test}" \
	PYTHONPATH=. \
	pytest -v -m integration tests/integration

migrate-up: ## Применить миграции Alembic до head
	alembic upgrade head

migrate-down-1: ## Откатить одну миграцию Alembic
	alembic downgrade -1

# ========================
# Code Quality
# ========================

format: ## Автоматическое форматирование кода (isort + black)
	isort .
	black .

lint: ## Проверка стиля и типов (flake8 + mypy)
	flake8 .
	mypy .

check: format lint test ## Полная проверка качества кода

# ========================
# Pre-commit
# ========================

precommit: ## Запуск pre-commit хуков на всех файлах
	pre-commit run --all-files

# ========================
# Help
# ========================

help: ## Показать список доступных команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
