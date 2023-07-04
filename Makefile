build:
	docker-compose build

init:
	docker-compose run --rm --entrypoint "python main.py --init" taxii_integration && docker-compose restart medallion && echo "Waiting for services to be ready..." && sleep 60 && echo "Done."

run:
	docker-compose run --rm taxii_integration --network datalake_taxii_integration