build:
	docker compose build

init:
	docker network create datalake-taxii || echo "Using previously created network datalake-taxii..." \
	&& docker compose run --rm --entrypoint "python main.py --init" taxii_integration \
	&& docker compose restart medallion

run:
	docker compose run --rm taxii_integration

test:
	docker network create test-datalake-taxii || echo "Using previously created network test-datalake-taxii..." \
	&& docker compose -f docker-compose.test.yml up -d -V nginx_proxy \
	&& docker compose -f docker-compose.test.yml run --entrypoint "python main.py --init" taxii_integration \
	&& docker compose -f docker-compose.test.yml restart medallion \
	&& docker compose -f docker-compose.test.yml run --entrypoint=sh taxii_integration -c \
	"python -m flake8 . --count --max-complexity=10 --max-line-length=120 --show-source --statistics && python -m pytest -s " \
	&& docker compose -f docker-compose.test.yml down
