build:
	docker compose build

init:
	docker compose run --rm --entrypoint "python main.py --init" taxii_integration && docker compose restart medallion

run:
	docker compose run --rm taxii_integration

test:
	docker compose up -d -V nginx_proxy && docker compose run --entrypoint "python main.py --init" taxii_integration && docker compose restart medallion && docker compose run --entrypoint=sh taxii_integration -c "python -m flake8 . --count --max-complexity=10 --max-line-length=120 --show-source --statistics && python -m pytest -s "