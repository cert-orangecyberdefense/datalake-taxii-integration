# Datalake Taxii Integration

 This repository is used to continuously retrieve threats from the Datalake platform and insert them into a taxii server. The user can set a frequency at which the collections of STIX objects will be updated. Upon each update, all previously stored objects are purged from the collections and then replaced by the updated objects, allowing us to provided new information collected on older threats, e.g. updated score or whitelisting.

A reference taxii server, [medallion](https://github.com/oasis-open/cti-taxii-server/) is used by default.

## Setting up the images

By default the taxii server is defined as `my.taxii_server.com`. It'll be resolved as the front nginx for each container defined in the docker-compose.`localhost` __cannot__ be used.

Instead, you can replace it with the `hostname` of the machine to access the taxii server from outside of the docker container. To do so you need to change `my.taxii_server.com` value in `docker-compose.yml`, `.env`, `deployment_sample`, `nginx_proxy`, `conf.d` and `proxy.conf`.

#### Step by step

1. If you don't want to clone this repo, copy the [example docker-compose file](docker-compose.yml.example) and rename it to `docker-compose.yml`, else just use the local `docker-compose.yml`. No matter what you choose here, you will have to complete the following steps.
2. Create a file named `.env` and copy the content of `template.env` into it, then fill the values like the following:

```
PYTHONUNBUFFERED=1
OCD_DTL_API_ENV=prod
OCD_DTL_USERNAME=user@mail.com
OCD_DTL_PASSWORD=mysupersecretpassword1
OCD_DTL_API_LOG_LVL=20
OCD_DTL_TAXII_HOST=http://my.taxii_server.com:8080
OCD_DTL_TAXII_MONGO_URL=mongodb://root-username-in-docker-compose:password-in-docker-compose@mongo:27017/
OCD_DTL_TAXII_USER=mytaxiiuser
OCD_DTL_TAXII_PASSWORD=mysupertaxiipassword1
OCD_DTL_TAXII_VERIFY_SSL=False
```

Make sure to replace the values.

3. Create a file named `medallion_config.json` and copy the content of `template_medallion_config.json` into it, then fill the value like the following:

 ```json
 {
    "backend": {
      "module_class": "MongoBackend",
      "uri": "mongodb://root-username-in-docker-compose:password-in-docker-compose@mongo:27017/"
    },
    "users": {
      "mytaxiiuser": "mysupertaxiipassword1"
    },
    "taxii": {
      "max_page_size": 100
    }
  }
 ```

:warning: Values must be synced with the content of `docker-compose.yml` and `.env`.In particular username and password of mongo, as well as `TAXII_USER` and `TAXII_PASSWORD`.

4. Create a file named `queries.json` and copy the content of `template_queries.json` into it, then fill the value like the following:

```json
{
    "queries": [
      {
        "comment": "daily query",
        "query_hash": "c86898ecf681cea394521d51499296a5",
        "frequency": "24h",
        "collection_id": "my_collection"
      }
    ]
  }
```

:warning: query hashes for the queries can be either retrieved on [Datalake](https://datalake.cert.orangecyberdefense.com/gui/) after a search in the url, or with the API on the following endpoint : `https://datalake.cert.orangecyberdefense.com/api/v2/mrti/advanced-queries/threats/`. The latter requiring you to already have a query_body, we recommend using the GUI.

5. Copy the [deployment_sample directory](deployment_sample) locally to configure nginx.  
6. Initialise the taxii db with:

```shell
make init
```

7. Then start ingesting threats with:

```shell
make run
```

## Stopping the container

To stop the container gracefully, allowing all the threats to be fully inserted, use:

```shell
docker stop -t 120 <container_name>
```

## Enable persistence

To keep data between reboot, uncomment and fill the mongo and redis `volumes` fields.

## Security

If you are on an open network, you must secure connections to the taxii server with a certificate, from [let's encrypt](https://letsencrypt.org/) for example.  
By default, nginx use an auto-signed certificate. Replace it in the [following directory](deployment_sample/certs), as well as change [the nginx config](deployment_sample/nginx_proxy/conf.d/proxy.conf) to not listen to 8080.  
Remember to adapt your `.env` after that.

:warning: by default medallion use credentials in plain text, therefore medallion_config.json must be secured.

## Testing

Before running tests you will need to change somes values in the `docker-compose.yml` file.

Replace the `taxii_integration` service with the following:

```yml
  taxii_integration:
    build: .
    restart: unless-stopped
    container_name: taxii_integration
    volumes:
      - ./tests/ci_files/queries.test.json:/code/queries.json
      - data_volume:/code/output
    env_file: ./tests/ci_files/.env.test
    depends_on:
      - nginx_proxy
    networks:
      - datalake_taxii_integration
```

Replace `medallion` service with the following:

```yml
  medallion:
    image: ocddev/cti-taxii-server
    container_name: medallion-deployment-sample
    restart: unless-stopped
    command: "uwsgi --ini /deployment_sample/uwsgi.ini"
    volumes:
      - ./tests/ci_files/medallion_config.test.json:/opt/taxii/config.json
      - ./deployment_sample/uwsgi.ini:/deployment_sample/uwsgi.ini
    depends_on:
      - mongo
    networks:
      - datalake_taxii_integration
```

This will change which files are used to build those services for our tests.

You can now run the following command:

```shell
make test
```
