# Datalake taxii integration

### This repository is used to continuously retrieve threats from the Datalake platform and insert them into a taxii server

A reference taxii server, [medaillon](https://github.com/oasis-open/cti-taxii-server/) is used by default

## Setting up the images
> By default the taxii server is defined as `my.taxii_server.com`. It'll be resolved as the front nginx for each container defined in the docker-compose.
`localhost` can __not__ be used.  
> Instead, you can replace it with the `hostname` of the machine so as to access to the taxii server from outside of the docker.
To do so you need to change the `my.taxii_server.com` value in _docker-compose.yml_, _.env_ and _deployment_sample/nginx_proxy/conf.d/proxy.conf_.

* Copy the [example docker-compose file](docker-compose.yml.example) and rename it to `docker-compose.yml` if you don't want to clone this repo, else just use the local `docker-compose.yml` 
* Copy the template.env to .env and fill the value
* Copy the template_medaillon_config.json to medaillon_config.json and fill the value.
  * Values must be synced with the content of docker-compose.yml and .env.  
    In particular username/password of mongo, as well as `TAXII_USER` and `TAXII_PASSWORD`
* Copy the template_queries.json to queries.json and fill the value
* Copy the [deployment_sample directory](deployment_sample) locally to configure nginx.  
* If needed, initialise the taxii db with:
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
By default, nginx use an auto-signed certificate. Replace it in the [following directory](deployment_sample/certs), as well as change [the nginx config](deployment_sample/nginx_proxy/conf.d/proxy.conf) to not listen to 8080.  
Remember to adapt your .env after that.

As well, by default medallion use credentials in plain text, therefore medaillon_config.json must be secured.
