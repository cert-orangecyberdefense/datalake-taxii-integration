import os

incorrect_config_message = 'Config seems incorrect, please check again your env variables'

OCD_DTL_API_ENV = os.getenv('OCD_DTL_API_ENV', 'prod')
assert OCD_DTL_API_ENV in ('prod', 'preprod'), incorrect_config_message

OCD_DTL_API_LOG_LVL = int(os.getenv('OCD_DTL_API_LOG_LVL', 30))  # 20 -> INFO, 30 -> WARNING
assert 0 <= OCD_DTL_API_LOG_LVL <= 50, incorrect_config_message

# Max result to retrieve from Datalake per query
OCD_DTL_NB_THREAT_PER_BATCH = int(os.getenv('OCD_DTL_NB_THREAT_PER_BATCH', 100))
assert 0 < OCD_DTL_NB_THREAT_PER_BATCH <= 5000, incorrect_config_message

OCD_DTL_QUERY_CONFIG_PATH = os.getenv('OCD_DTL_QUERY_CONFIG_PATH', 'queries.json')

OCD_DTL_TAXII_MONGO_URL = os.getenv('OCD_DTL_TAXII_MONGO_URL')
OCD_DTL_TAXII_HOST = os.getenv('OCD_DTL_TAXII_HOST', 'http://nginx_proxy:8081')
OCD_DTL_TAXII_PASSWORD = os.getenv('OCD_DTL_TAXII_PASSWORD')
OCD_DTL_TAXII_USER = os.getenv('OCD_DTL_TAXII_USER')
OCD_DTL_TAXII_GROUP = os.getenv('OCD_DTL_TAXII_GROUP', 'default-taxii-group')

OCD_DTL_REDIS_HOST = os.getenv('OCD_DTL_REDIS_HOST', 'redis')
OCD_DTL_REDIS_PORT = os.getenv('OCD_DTL_REDIS_PORT', 6379)
OCD_DTL_REDIS_PASSWORD = os.getenv('OCD_DTL_REDIS_PASSWORD')
