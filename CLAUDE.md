# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ※ 실습용 예시: `/init`이 만들어 내는 전형적인 초안입니다. 실제 생성 결과는 버전·환경에 따라 다릅니다.
> 다음 커밋(2-2)에서 이 초안을 사람이 직접 다듬습니다. 두 커밋의 diff를 비교해 보세요.

## Project Overview

This is an Order Service, a simple order management REST API built with FastAPI and SQLite.
It provides endpoints for managing products and orders.

## Development Commands

### Setup
```bash
pip install -r requirements.txt
python scripts/seed.py
```

### Running the Application
```bash
uvicorn app.main:app --reload
```

### Testing
```bash
pytest
```

### Resetting the Database
```bash
python scripts/reset_db.py
```

## Architecture

The application follows a layered architecture:

- `app/main.py` - FastAPI application entry point; registers routers and initializes the database
- `app/api/` - API route handlers
  - `orders.py` - Order endpoints (list, get, create)
  - `products.py` - Product endpoints
- `app/services/` - Business logic
  - `order_service.py` - Order creation and retrieval logic, coupon handling
- `app/models.py` - Pydantic models for request/response validation
- `app/db.py` - Database connection management and migration runner
- `migrations/` - SQL migration files applied in order
- `scripts/` - Utility scripts for seeding and resetting the database
- `tests/` - Pytest test suite

## Database

The application uses SQLite. The database path is configured via the `APP_DB` environment variable
(defaults to `data/app.db`). Migrations are applied automatically on startup.

Tables:
- `products` - id, name, price
- `orders` - id, order_no, customer, total, created_at, status, cancelled_at
- `order_items` - id, order_id, product_id, qty, unit_price

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write clean, readable, and maintainable code
- Add docstrings to public functions
- Keep functions small and focused
- Handle errors appropriately

## Testing Guidelines

- Write tests for new features
- Use the `client` fixture from `conftest.py` for API tests
- Tests use a temporary database

## Important Notes

- Order numbers follow the format `A-XXXX`
- Coupons are defined in `order_service.py`
