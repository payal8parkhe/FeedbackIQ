.PHONY: up down test eval lint migrate seed clean

up:
	docker compose up --build -d

down:
	docker compose down

test:
	pytest backend/tests -v

test-unit:
	pytest backend/tests/unit -v

eval:
	python -m app.evaluation.runner --split dev --report-out docs/eval_dev_report.json

eval-test:
	python -m app.evaluation.runner --split test --report-out docs/eval_test_report.json

eval-compare:
	python -m app.evaluation.compare --base docs/eval_dev_report.json --candidate docs/eval_test_report.json

lint:
	ruff check backend
	mypy backend/app

seed:
	python scripts/seed_demo.py --reviews 100

migrate:
	alembic -c backend/alembic.ini upgrade head

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
