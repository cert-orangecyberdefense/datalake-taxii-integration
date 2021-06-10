# Datalake taxii integration

### This repo is used to continuously retrieve threats from the Datalake platform and insert them into a taxii server

A reference taxii server, [medaillon](https://github.com/oasis-open/cti-taxii-server/) is used by default

## Setting up the images
* Copy the [example docker-compose file](docker-compose.yml.example) and rename it to `docker-compose.yml` if you don't want to clone this repo, else just use the local `docker-compose.yml` 
* Copy the template.env to .env and fill the value
* Copy the template_medaillon_config.json to medaillon_config.json and fill the value.
  * values must be synced with the content of docker-compose.yml and .env
* Copy the template_queries.json to queries.json and fill the value
* if needed, initialise the taxii db with:
```shell
docker-compose run --entrypoint "python main.py --init" taxii_integration && docker-compose restart medallion 
```
* Then start ingesting threats with:
```shell
docker-compose run taxii_integration
```

## Stopping the container

To stop the container gracefully, allowing all the threats to be fully inserted, use:
```shell
docker stop -t 120 <container_name>
```

## Enable persistence

To keep data between reboot, uncomment and fill the mongo and redis `volumes` fields. 

## Security

If you are on an open network, you must secure connections to the taxii server with a certificate, from let's encrypt for example.

As well, by default medallion use credentials in plain text, therefore [this file](medaillon_config.json) must be secured.
